# S286 — Jira drafts

Status: drafts only, nothing posted, no status changed. The tech lead approves, then the orchestrator posts.

Read before drafting (20/11 ~09:00 +07):

- Open issues `project in (PR, KAN, CON) AND statusCategory != Done`: 100+ rows; the ones touched lately are the app
  epics PR-22..PR-27, PR-20, PR-29, PR-30 (all updated 16–19/11). KAN/CON rows are the AA content and marketing boards
  (last activity ≤ 13/11), not targets for these drafts.
- Newest comments read: PR-22 10679 (19/11, admin on phones), PR-23 10675 (19/11, Content studio facts lock, AI
  allowance, bill card), PR-25 10677 (19/11, Booking in Vietnamese) and the PR-25 comments back to 06/11, PR-20 10661
  (kỳ 5, 15/11). None of them covers the items below: My work, staff role presets, tour drafts and lock, Booking
  finance reads and make/approve split, the supply model, or the AI disclosure on published posts. The 08/11
  "AI-assisted" label (PR-23/PR-25) was about labels inside the apps; E3 is about the published post itself.
- Updated ~09:40 +07 by the orchestrator: Booking #290 and #291 merged and deployed, second live pass done, one
  sign-in passed, Staff presets checked on screen by the tech lead.

No PR-20 draft today: kỳ 5 was posted Sunday 15/11 (comment 10661) and covers 10–16/11; kỳ 6 (17–23/11) is due one
week later, Sunday 22/11 (memory `platform-report-weekly`, cadence rule S253). Carry-over notes for kỳ 6 at the end.

When posting: `contentFormat: html`, `@thule` as the mention node
(`<span data-type="mention" data-user-id="70121:5793bdd5-44b1-4623-97d4-43c35d440869">@thule</span>`), markdown
tables → HTML tables (a table never inside a list item: PR-24 400 on 19/11), screenshots uploaded and embedded in the
listed order. Screenshot paths are relative to `docs/audits/2026-11-20-S286-session/`.

---

## E1 — PR-22 (CIS admin): My work for content staff; tour edits as drafts with a review gate and a lock; staff role presets

Why: CIS admin features for AA staff, shipped 20/11 (CIS #1615, #1617; tour versions CIS #1598/#1599 shipped 19/11,
proven live 20/11). PR-22's last comment is 19/11 (admin on phones), nothing on these.

Text:

@thule Cập nhật trang quản trị CIS ngày 20/11 (Dev):

1. **Trang "My work" cho nhân viên nội dung:**
   - Nhân viên nội dung đăng nhập là vào thẳng trang này. Mỗi ô là một hàng việc đang chờ: tour chờ duyệt (Review Queue), bản nháp mô tả nhà cung cấp, khách sạn và dịch vụ chưa có mô tả, bản nháp nội dung AA.
   - Bấm một ô là mở đúng trang đó với bộ lọc sẵn, số trên ô bằng số trên trang.
   - Đã thử 20/11 bằng tài khoản nội dung thử: 73 / 8 / 0 / 1 việc (tổng 82), bấm từng ô thì số trên trang khớp 4/4; trên máy tính và điện thoại, nền sáng và tối, không lỗi.
   - Quản trị viên vẫn vào trang Overview như cũ; My work có trong menu và thấy thêm 2 ô: thẻ địa điểm chờ duyệt và nội dung bị giữ vì tuân thủ. Kiểm lại 20/11 sau bản sửa: bấm ô thẻ địa điểm mở đúng danh sách đã lọc, 4.859 = 4.859.
2. **Sửa tour AA có phiên bản, cổng duyệt và khoá:**
   - Sửa dữ liệu nguồn của tour được ghi lịch sử: ai sửa, lý do, giá trị trước và sau.
   - Sửa câu chữ tạo một bản nháp mới, ghi lý do, người sửa và các chữ đã đổi; bản đang bán không bị đụng tới cho tới khi công bố.
   - Bản nháp chưa qua bước kiểm lại thì không công bố được.
   - Tour đã công bố bản sửa tay được khoá: bước viết lại tự động bằng AI bỏ qua tour đó, chạy lại một tour bị từ chối, xuất tự động bị chặn. Không tốn tiền AI.
   - Có công tắc bắt buộc người thứ hai công bố (trên Dev đang tắt).
   - Đã kiểm 20/11 trên một tour thật của Dev, trong một lượt thử được hoàn tác, không để lại dữ liệu. Chưa thử qua màn hình: trang soạn tour đầy đủ là bước tiếp theo.
3. **Trang Staff:** mỗi nhân viên có 3 vai trò mẫu bấm một lần (Administrator, Business owner, Content + Product & operations); các vai trò chi tiết nằm sau nút "Show all roles"; form thêm nhân viên mới mặc định quyền thấp nhất (Content Team, không có quyền Booking). Đã kiểm trên màn hình 20/11 bằng tài khoản chủ nền tảng.
4. **Đăng nhập một lần:** đăng nhập CIS bằng tài khoản công ty xong, mở Booking là vào thẳng, không hỏi đăng nhập lại. Đã thử tự động 20/11 bằng tài khoản thử có quyền Booking (cấp tạm rồi thu hồi).

Ảnh theo thứ tự: (1) trang My work của nhân viên nội dung, (2) My work trên điện thoại.

Screenshots (upload names without diacritics):
1. `live/01a-my-work-content-1440-light.png` → `my-work-nhan-vien-noi-dung.png`
2. `live/01c-my-work-content-390-light.png` → `my-work-dien-thoai.png`

Do not attach `live/02a-staff-e2e-cs-drawer-readonly.png` (shows only the read-only notice for the test account) or
`live/01e-admin-overview-nav-1440-light.png` (not needed).

| Claim | Evidence |
|---|---|
| Content role lands on My work; 4 tiles 73 / 8 / 0 / 1, total 82 | `live/evidence.md` §A (07:30–07:55 +07); `live/data/01-my-work-content.json`; Linear AA-1156 comment 00:50Z |
| Tile = target page after a click, 4/4 for the content role | `live/evidence.md` §A table (Review 73, supply drafts 8, no description 0, AA drafts 1) |
| 1440 + 390, light + dark, 0 console errors, no horizontal scroll | `live/evidence.md` §A; `live/01a..01d` |
| Admin lands on Overview, My work in the nav | `live/evidence.md` §A; `live/01e` |
| Source edit history, draft version with reason / author / word diff, live version untouched | `aa1146-live-proof.jsonl` steps `raw_edit_revision_row`, `draft_version_created`; Linear AA-1146 comment 23:02Z 19/11 (= 06:02 +07 20/11) |
| Unchecked draft refused | `gate_refuses_unchecked_draft` 409 `revalidate_required` |
| Locked after publish; S1 job skips, run-tour refused, automatic export refused, $0 | steps `published_and_master_locked`, `s1_job_skips_locked_tour`, `run_tour_refuses_locked_tour`, `export_refuses_automatic_exit`, `no_paid_path_reached` |
| Two-person switch exists, off on Dev | `aa1146-live-proof.jsonl` `two_person_publish_switch: false`; AA-1146 S285 comment (cis.content.publish_two_person) |
| Rolled back, nothing left | `rolled_back_nothing_persists` (0 drafts, 0 revisions, 0 locks) |
| Admin extra tiles; Place cards 4,859 = 4,859 after the fix | `live/evidence.md` "S286 second pass" B; `live/08-...png`; `data/08-cis-my-work-recheck.json` (CIS #1620) |
| Staff presets / Show all roles / least-privilege default, checked on screen | tech lead's owner-session screenshots 20/11 ~09:00 (chat); AA-1150 comment 02:08Z |
| One sign-in CIS → Booking, no second prompt | `one-sign-in.spec.ts` PASS 19.4 s; `live/05a`, `live/05b`, `data/05-one-sign-in-hops.json`; grant applied and revoked by the tech lead |

Not claimed on purpose:
- The S1 batch skip of a locked tour (Batch is switched off on Dev, answered 503; covered by CI tests only).

---

## E2 — PR-25 (Booking): finance staff read access; making and approving separated; supply model proof

Why: Booking #288 merged and deployed 20/11 (finance reads, make/approve split), checked live on the Booking staff admin
with the test finance account; the supply model (Booking #281/#282, shipped 19/11) proven live on Dev today. PR-25's
last comment is 19/11 (Vietnamese UI), nothing on these.

Text:

@thule Cập nhật Booking ngày 20/11 (Dev):

1. **Quyền của kế toán:** nhân viên kế toán xem được hoá đơn nhà cung cấp, giá, nhà cung cấp, vận hành, hồ sơ chuyến đi và danh mục tour, nhưng không sửa được. Kế toán không kích hoạt nhà cung cấp, không công bố hợp đồng, không duyệt dừng bán và không ghi khoản chi trả. Đã thử 20/11 bằng tài khoản kế toán thử: các trang trên mở được; danh sách nhà cung cấp và chi tiết một nhà cung cấp đang ngưng không có nút kích hoạt hay công bố.
2. **Tách người làm và người duyệt:** kích hoạt nhà cung cấp, công bố hợp đồng và duyệt dừng bán là các quyền riêng, tách khỏi quyền nhập liệu. Đã thử 20/11: người tạo hợp đồng không tự công bố được, người thứ hai công bố thì hợp đồng có hiệu lực, sau đó điều khoản hợp đồng bị khoá.
3. **Hợp đồng nhà cung cấp tính giá trẻ em, ngày dừng bán và phí huỷ** (kiểm 20/11 trên Dev bằng một hợp đồng thử, không lưu lại; kiểm trực tiếp trên hệ thống, chưa qua màn hình):

| Điều khoản trong hợp đồng thử | Kết quả |
|---|---|
| Giá trẻ em 50 % giá người lớn | Người lớn 40 USD, trẻ em 20 USD; gia đình 2 người lớn + 1 trẻ em 100 USD |
| Dừng bán ngày 24/12 | 23/12 và 25/12 vẫn bán bình thường; 24/12 chuyển thành "theo yêu cầu" (on request), dòng báo giá ngày đó ghi lý do dừng bán |
| Phí huỷ theo bậc | Huỷ trước 30 ngày trở lên: 0 %; 15–29 ngày: 50 %; dưới 15 ngày: 100 % |

Dừng bán chỉ đặt được trên hợp đồng đã công bố, do nhân viên hợp đồng hoặc quản trị viên đặt; có hiệu lực ngay và chờ người khác xem lại.

4. **Duyệt giá cũng tách khỏi nhập giá** (20/11): duyệt hoặc từ chối quy tắc giá, tỷ giá, chính sách huỷ, chiết khấu đại lý, bảng giá hợp đồng và điều chỉnh giá theo chuyến là quyền riêng; duyệt và kết thúc allotment, kích hoạt khách sạn và dịch vụ cũng vậy. Người nhập vẫn tự rút được yêu cầu đang chờ của chính mình; khách sạn và dịch vụ do người không có quyền kích hoạt tạo ra sẽ ở trạng thái chờ duyệt. Kiểm bằng bộ test tự động trên cơ sở dữ liệu thật, chưa thử qua màn hình.
5. **"My work" trên trang chủ Booking** (20/11): một dải ô theo quyền của từng người, chia hai nhóm "To do" và "To approve or pay" (hồ sơ chuyến của tôi, kiểm tra chuyến quá hạn, dòng B2B theo yêu cầu, hoá đơn nhà cung cấp quá hạn và sắp đến hạn, hoá đơn đại lý quá hạn, hoá đơn chờ duyệt, chờ chi, thanh toán đại lý chờ duyệt, dừng bán chờ xem lại). Ô duyệt chỉ đếm việc người đó được phép duyệt (không đếm việc chính mình nhập). Đã thử 20/11: quản trị viên 10 ô, kế toán 6 ô; bấm từng ô mở đúng danh sách đã lọc, số khớp (kiểm tra chuyến quá hạn 18 = 18, dòng theo yêu cầu 3 = 3, các ô còn lại 0 = 0 trên Dev); máy tính và điện thoại, nền sáng và tối.

Ảnh: (1) dải My work trên trang chủ Booking.

(End of comment text.)

Screenshot (upload name without diacritics):
1. `live/06-booking-my-work-admin-1440-light.png` → `booking-my-work.png` (shows only the band, no supplier names).

Screenshots: none attachable as they are. `live/03a-booking-suppliers-finance-1440-light.png` and
`live/03b-booking-supplier-inactive-detail-finance-1440-light.png` prove item 1 but show synthetic supplier names that
carry internal issue ids (AA-835, AA-682, AA-1091, "S280", "live check, not real"). Options: post without images
(text above already says so), or crop `03a` to the header + KPI cards (top ~330 px: "Finance" user, Suppliers page)
and post that one with the line "Ảnh: (1) trang Nhà cung cấp khi đăng nhập bằng tài khoản kế toán." — the crop does
not show the missing buttons, so the claim still rests on the evidence file.

| Claim | Evidence |
|---|---|
| Finance reads bill / pricing / supply / ops / trip case / catalog; no payout.write, supplier.activate, contract.publish, stop_sale.approve | `live/evidence.md` §C; `live/data/03-booking-finance.json`; Linear AA-1150 comment 00:50Z |
| Pages open (supplier bills, pricing rules, suppliers, trip cases → 200), no Activate / Publish on list and inactive detail | `live/evidence.md` §C; `live/03a`, `live/03b` |
| Activation / publish / stop-sale review are separate rights | Booking #288 (merged 00:17Z, deployed `f8c89580`); `staff/me` permission list |
| Maker cannot publish own contract; second person publishes; terms locked after | `aa1145-live-proof.jsonl` `maker_cannot_publish` (maker_checker), `contract_published_by_checker`, `terms_fixed_after_publish` (contract_locked) |
| Child 50 %: 40 → 20; family 2A+1C = 100 | `child_line_is_50_pct`, `family_line_2a_1c` |
| Stop-sale 24/12 → on_request, 23/12 and 25/12 available; quote line note | `availability_check`, `quote_line_24_12_on_request` |
| Tiers ≥30 d 0 %, 15–29 d 50 %, <15 d 100 % | `cancellation_tiers_fee_pct` (45/30 → 0, 20/15 → 50, 7/0 → 100) |
| Stop-sale only on a published contract; set by contracting / admin; in effect, pending review | `stop_sale_on_draft_refused`, `permission_map_stop_sale_write`, `stop_sale_set_by_contracting` (pending, in_effect) |
| Nothing left | `rolled_back_nothing_persists`; Linear AA-1145 comment 22:49Z 19/11 (= 05:49 +07 20/11) |
| Pricing / allotment / hotel-service approvals split; maker withdraws own pending; maker-created hotel/service inactive | Booking #290 merged + deployed `cfc49b5a`; integration tests `test_aa1155_approve_split.py` (CI) |
| Booking My work: admin 10 tiles, finance 6; tile = list (18 = 18, 3 = 3, others 0 = 0); 1440/390 light/dark | `live/evidence.md` "S286 second pass" A; `live/06*`, `live/07*`; `data/06-07`; Booking #291 `b71fca9c` |

Not claimed on purpose:
- "Sales cannot set a stop-sale" over HTTP: covered by CI tests, not run live.
- A maker without the activation right creates an inactive supplier (review fix in #288): shipped, not exercised live.
- Deposit 30 % stored in the terms: saved, not used in a calculation in the proof.

---

## E3 — PR-23 (Content studio): AI disclosure line and machine mark on published posts and exports

Why: shipped 20/11 (CIS #1619, Partner #369), run live end to end on the test WordPress site and the test Facebook
Page. It changes what agencies' readers see on every AI post. PR-23's last comment is 19/11, nothing on this.

Text:

@thule Bài viết AI của đại lý giờ được ghi rõ là có AI hỗ trợ (20/11, Dev), theo yêu cầu minh bạch của Đạo luật AI của EU (Điều 50):

- **WordPress:** cuối mỗi bài có dòng "This content was created with the help of AI.", kèm nhãn ẩn trong mã trang để máy đọc được (công cụ, mô hình, thời điểm tạo, có người sửa hay không). Đã thử 20/11 trên site WordPress thử: đăng một bài, dòng công khai hiện ở cuối bài; gỡ bài xong site không còn bài đó.
- **Facebook:** cuối bài có cùng dòng công khai và thẻ #AIgenerated. Đã thử 20/11 trên Page thử: đăng, đọc lại bài trên Facebook thấy đúng dòng cuối, rồi xoá bài. Không chụp ảnh Page.
- **Bản xuất dạng văn bản:** cuối file có dòng công khai và một dòng đánh dấu cho máy đọc. Đã thử 20/11.
- **Xuất CSV ở trang My Tours:** thêm 4 cột (AI generated, AI generator, thời điểm tạo, có người sửa hay không) ở cuối, các cột cũ giữ nguyên thứ tự; dòng cuối file là dòng công khai. Đã thử 20/11: chọn 2 tour, tải CSV. File XLSX có cùng các cột, chưa mở thử.
- Không tốn tiền AI, không tạo bài mới: dùng 2 bài đã viết sẵn của đại lý thử, đăng xong đã gỡ, 2 bài trở về trạng thái sẵn sàng đăng.

Ảnh theo thứ tự: (1) cuối một bài trên site WordPress thử, dòng công khai được khoanh đỏ, (2) nút tải CSV trên trang My Tours, (3) file CSV vừa tải với 4 cột AI và dòng công khai ở cuối.

Screenshots (upload names without diacritics):
1. `live/aa1168-01-wordpress-post-disclosure.png` → `wordpress-dong-cong-khai-ai.png`
2. `live/aa1168-02-my-content-csv-button.png` → `my-tours-nut-csv.png`
3. `live/aa1168-03-my-catalog-csv-columns.png` → `csv-cot-ai.png`

| Claim | Evidence |
|---|---|
| WordPress: disclosure paragraph ends the article + machine mark; unpublished, post in trash / not public | `live/aa1168-evidence.md` §1 (01:30–01:50Z); screenshot 1 |
| Facebook: message ends with disclosure + #AIgenerated; deleted, Graph read 400 after | `live/aa1168-evidence.md` §2 (Graph read-back; no screenshot: the test Page is the tech lead's own) |
| Text export: disclosure + `AI-Content:` line, `X-AI-Generated` header | `live/aa1168-evidence.md` §3 |
| CSV on My Tours: 4 AI columns last, old order kept, last line = disclosure | `live/aa1168-evidence.md` §4 (Playwright UI download, read-only guard); screenshots 2, 3 |
| XLSX not opened | `live/aa1168-evidence.md` §4 last bullet |
| $0, nothing generated, both pieces back in Ready to Publish, channels untouched | `live/aa1168-evidence.md` "Cleanup and end state"; Linear AA-1168 Done |

Note: the page is "My Tours" (`/portal/tours/mine`) in the UI; the evidence file calls it "My Content".

---

## Left out on purpose

- **AI spend re-check 26/26 and the job cost fix** (doubled cost on 9 proof jobs, corrected): internal cost detail and
  an error already fixed (skill rule 7). If the tech lead wants one line in kỳ 6: "Số chi phí AI trên mọi trang quản
  trị đã đối chiếu lại với sổ ghi từng lượt gọi: 26/26 khớp (20/11)." (source `aa1127-ledger-recheck.txt`,
  06:03 +07 20/11). Test-data renaming: internal.
- **Security and compliance review (ISO 27001 / SOC 2 / ISO 42001 / OWASP) and the 12 decisions**: tech lead's call
  (memory `jira-no-tech-decisions`), no draft.
- **Lawyer timing (D6) / DPA**: Ms. Thư already saw "Điều khoản và Quyền riêng tư bản nháp v0.6, vẫn ghi chờ luật sư
  xem" in kỳ 5 (15/11), and progress comments carry no questions to her (memory `jira-draft-tone`, S270). Not drafted
  now. If the tech lead wants it raised, one neutral line for the kỳ 6 report (not a question, no date): "Hồ sơ xử lý
  dữ liệu cho đại lý (DPA) và Điều khoản đã có bản nháp; thời điểm nhờ luật sư xem do chị quyết, phần kỹ thuật vẫn làm
  tiếp bình thường."
- **Lean repo guard, Cognito groups, custom roles foundation (CIS 462 / bk-062), Terraform drift**: infrastructure.

## Carry-over for kỳ 6 (PR-20, due Sunday 22/11, covers 17–23/11)

Material from 20/11 to fold in: E1–E3 above (as one line each, linking PR-22 / PR-25 / PR-23); the T9 blog first-pass
yield follow-up (quality, still open); the plan items from kỳ 5 "Kế hoạch tuần tới" to mark done / not done. Numbers
must be re-read on the day of the report (content funnel, AI and DataForSEO month to date).

## Posted (tech lead "đăng", 20/11 ~10:20 +07)

- E1 → PR-22 comment **10681** (2 images inline).
- E2 → PR-25 comment **10682** (1 image inline).
- E3 → PR-23 comment **10683** (3 images inline).
