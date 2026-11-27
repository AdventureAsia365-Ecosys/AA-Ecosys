# S295 meeting prep synthesis (26/11, meeting 11:00 +07)

Sources: four read-only lanes (code-trace, ui-labels, tickets, demo-tour) plus my own spot checks of the disputed points:
- `apps/AA-Booking/backend/app/b2b/tariff.py:1-30`: the agency tariff never reads the hand matrix amount. It prices components.
- `apps/AA-Booking/backend/app/catalog/price_workbench.py:22-24,447-460`: Make sellable skips `no_components`, `not_in_catalog` and `no_approved_price`.
- `apps/AA-Booking/backend/app/catalog/trip_plan_prices.py:554-578`: `price_ready` = a matrix row still valid today, computed or from a published version.
- `apps/AA-CIS-App/api/services/settings_registry.py:486-494`: a setting cannot be self-approved while two-person approval is on, or while the publish switch is already on.

Runbook line numbers refer to `.tmp-session/S295/code-trace/runbook.txt`, the text of `docs/audits/2026-11-25-S294-session/meeting-runbook.html`.

## 1. GO / NO-GO per segment

| Segment | Verdict | Why |
|---|---|---|
| Pricing demo (SYNTHETIC supplier → From $X) | **CONDITIONAL GO** | The code chain works for the business owner alone. Three things are not proven yet: (a) no demo tour is picked, because the finder script was not run; (b) whether an approved b2b rule with an RRP markup is in force (without it, no "From $X" appears); (c) whether her Booking grant is `admin`. If (b) fails, the demo stops at Price setup and the tech lead must act as second person on the rule. Changing the tour does not help (rules are global, `pricing/repository.py:22-30`). |
| SUP-000019 bank approval + 24 h lock | **GO** | Needs: Booking `admin` grant, a call-back note of 10 to 500 characters, and no contact change on SUP-000019 in the last 30 days by her or by the person who entered the account (otherwise 409 `contacts_recently_changed`). This is an ordinary second-person approval, not a self-approval, so it will **not** appear under Audit Log › Business-owner self-approvals. The lock probe on BIL-000002 should return 409 `bank_payout_locked`. |
| Two-person settings (cis.content.publish_two_person, cis.settings.two_person_approval) | **GO, order fixed** | Turn on `cis.content.publish_two_person` first, then `cis.settings.two_person_approval`. In the reverse order the second switch needs a second person. Both are Off today, under different area tabs (Content, Platform). |
| Staff login AA-1155 (business owner + shared content/booking mailbox) | **CONDITIONAL GO** | The owner flow is fine (CIS sign-in first, then the tech lead sets the marker, then reload Booking after ~1 min). Linear AA-1155 (23/11) says the shared mailbox account has no Booking role. Jira 10691 (24/11) tells her it has "Product, ops & accounting". Check the Booking column on CIS Staff before 11:00. |
| ISMS approval + red-team review (AA-1166) | **NO-GO for the ISMS approval as written; GO for red-team numbers** | The red-team numbers match Linear and Jira 10710. The runbook gives no link to the ISMS pack and no place to record her approval and its date. She has never been sent the pack. |
| View-as (AA-1157) | **GO, role names fixed** | Only a platform owner sees "View as" (the tech lead's own session is the remaining Done-when item). The runbook's "Content + Product & operations" is a Staff-page preset, not a view-as role. Pick CIS "Content" and Booking "Product, ops & accounting". |

## 2. Blockers and mismatches (most important first), with runbook text changes

1. **The demo tour is not chosen** (blocker for the pricing demo). Runbook line 50:
   - Now: "Một NCC, một khách sạn, một giá, trên một tour chưa có giá."
   - Replace: "Một NCC, một khách sạn, một giá, trên một tour đang ở trạng thái No components (bước tiếp theo: Add hotels & services), mọi đêm ngủ cùng một nơi (ví dụ 2 ngày 1 đêm), và ở nơi đó chưa có khách sạn active nào. Tour đã chọn: <mã tour>, nơi nghỉ đêm: <tên nơi>."
   - Do not use a "Missing rates" tour: it already has components, gets no suggestion and stays Missing rates (`component_suggest.py:340-345`). Do not use the SYNTHETIC 3-day draft tour either: it is not in `catalog.v_tour`, so it has no trip plan, and it is reserved for AA-1148.
2. **Line 48: Make sellable condition is wrong, and ways 1 and 3 never let an agency quote.**
   - Now: "Sau khi có giá: Make sellable (cần version đã duyệt, còn hiệu lực hôm nay) và cột Can operate đạt thì đại lý mới báo giá được."
   - Replace: "Sau khi có giá: Make sellable cần tour đã gắn khách sạn / dịch vụ và có ít nhất một dòng giá còn hiệu lực hôm nay (tính từ giá NCC hoặc từ version đã duyệt); cột Can operate phải đạt thì đại lý mới báo giá được. Giá đại lý (báo giá, bảng giá CRM) luôn tính từ khách sạn, dịch vụ và giá NCC (cách 2); cách 1 và 3 chỉ đặt giá công khai From $X / RRP và bảng giá trong Booking."
   - Evidence: `tariff.py:24-27`, `price_workbench.py:22-24,453-458`, `trip_plan_prices.py:554-578`.
3. **Line 62: "Approve a pricing rule" can never show at this step.** Before hotels are added, the next step is always "Add hotels & services" (`price_workbench.py:149-163`).
   - Now: "Tìm tour. Nếu bước tiếp theo ghi "Approve a pricing rule" hoặc "Approve an exchange rate" thì dừng lại: tech lead làm người thứ hai."
   - Replace: "Tìm tour: bước tiếp theo phải là "Add hotels & services". Xem ô Pricing rule ở cột Checks (hoặc Supply › Pricing rules & FX); nếu chưa đạt thì dừng lại, tech lead làm người thứ hai. Giá bằng USD thì không cần tỷ giá."
4. **Line 56: wrong button label, and a hotel name that may not be suggested.**
   - Now: "Add hotel: Supplier SYNTHETIC price test, tên SYNTHETIC hotel, City / place = nơi nghỉ đêm của tour → Save hotel."
   - Replace: "Add hotel: Supplier SYNTHETIC price test 26-11, tên "SYNTHETIC hotel <nơi nghỉ đêm>", City / place = đúng nơi nghỉ đêm của tour (chọn trong danh sách) → bấm Add hotel ở cuối khung."
   - "Save hotel" appears only when editing (`HotelFormDrawer.tsx:105`). Putting the place in the name raises the score from 0.35 to 0.55, so an older hotel at the same place cannot win a tie.
5. **Line 64: accepting service suggestions breaks the price.** Service suggestions have no rates, so the tour goes to Missing rates.
   - Now: "Mỗi đêm, SYNTHETIC hotel được gợi ý → Accept → Save … hotel and service item(s)."
   - Replace: "Mỗi đêm, SYNTHETIC hotel được gợi ý → Accept; các gợi ý dịch vụ (xe, hướng dẫn viên…) bấm Reject → Save … hotel and service item(s). Nếu không thấy SYNTHETIC hotel: kiểm City / place của khách sạn có đúng nơi nghỉ đêm không."
6. **Line 52: name collision and field name.** The unique index on name + country includes inactive suppliers (`migrations/008_suppliers_contracts.sql:88-90`). A rerun or an old rehearsal gives 409 `supplier_exists`.
   - Now: "Add supplier: tên SYNTHETIC price test, loại Hotel, nước của tour đã chọn → Save supplier."
   - Replace: "Add supplier: tên SYNTHETIC price test 26-11, Categories chọn Hotel, nước của tour đã chọn → Save supplier."
7. **Line 59: missing save step.**
   - Now: "Tiêu đề SYNTHETIC contract, hiệu lực từ hôm nay, USD. Tab Rates → Add rate …"
   - Replace: "Tiêu đề SYNTHETIC contract, hiệu lực từ hôm nay, USD → Save as draft. Tab Rates (chọn đúng hợp đồng nháp) → Add rate phòng Double, ví dụ 50 USD/đêm. Menu dòng hợp đồng → Publish."
8. **Line 105: switch order.**
   - Now: "Bật duyệt hai người ở Platform › Settings: cis.content.publish_two_person và cis.settings.two_person_approval = On, lý do ≥ 20 ký tự."
   - Replace: "Bật duyệt hai người ở Platform › Settings, đúng thứ tự: trước tiên cis.content.publish_two_person (tab Content), rồi cis.settings.two_person_approval (tab Platform) = On, lý do ≥ 20 ký tự. Làm ngược thứ tự thì công tắc thứ hai phải chờ người thứ hai duyệt."
9. **Line 46: Excel limit is 300, not 50** (`price_import.py:70-72`).
   - Now: "Giá vào thành version nháp; tối đa 50 tour mỗi lần."
   - Replace: "Giá vào thành version nháp; tối đa 300 tour (2 MB) mỗi file; Recompute chạy tối đa 50 tour mỗi lần."
10. **Line 98: the RRP markup is not on Pricing policy.** It is the `rrp_markup_pct` field of the b2b rule.
    - Now: "Tất cả nằm trong Supply › Pricing policy và Agency tiers, …"
    - Replace: "Nằm trong Supply › Pricing rules & FX (mức cộng RRP), Agency tiers (chiết khấu hạng) và Pricing policy (cỡ nhóm, giữ chỗ, tuổi trẻ em, làm tròn, ngoại lệ); đổi được trên màn hình (luôn hai người duyệt). Hôm nay chỉ cần xem, không cần quyết."
11. **Line 108: view-as role names.**
    - Now: "View-as dưới vai "Content + Product & operations" trên CIS và Booking; mọi lệnh ghi phải ra 403."
    - Replace: "Tech lead (chủ nền tảng) View as: CIS vai "Content" (Roles & permissions › View as), Booking vai "Product, ops & accounting" (Roles › View as a role); mọi lệnh ghi phải ra 403."
12. **Line 107: ISMS has no link and no place to record the approval.**
    - Replace: "Chủ DN đọc <tên tài liệu, link> và duyệt bộ ISMS; ngày duyệt ghi vào <Linear AA-1166 + ISMS evidence index>. Kèm red-team AI đầu tiên (12 đạt, 1 báo nhầm, 3 chưa chạy, 0,39 USD)."
13. **Line 77: missing preconditions.**
    - Append: "Phải gõ ghi chú gọi lại (ai xác nhận, lúc nào) ít nhất 10 ký tự. Đây là duyệt người thứ hai bình thường (người khác đã nhập tài khoản), nên không hiện trong Business-owner self-approvals."
14. **Line 54: missing causes for "Activate (needs a second person)".**
    - Append: "…, hoặc tài khoản Booking của chủ DN chưa có quyền admin / contracting."
15. **Line 104 (AA-1155): mismatch between Linear and Jira on the shared mailbox account's Booking role.**
    - Append: "Trước khi đăng nhập, kiểm cột Booking của tài khoản này trên CIS › Staff & access; thiếu vai trò thì tech lead gán trước."
16. **Minor wording.**
    - Line 18: say "giá trị Yes" (they are policy rows with a Change button, not toggles). The second row is "The business owner may pay a bill she approved".
    - Line 67: "RRP for 2" is a label inside the Price column.
    - Line 69: TripPlanner can still show the old page on the first visit after ~30 min; reload once.
    - Line 32: the table leaves out add-on publish, billing entity change and bank account approval.

## 3. Before 11:00 (real prerequisites only)

1. **Pick the demo tour.** Run `.tmp-session/S295/demo-tour/find_demo_tour.py` (read-only, booking api container) and use the #1 candidate. This needs ECS exec, which this run's read-only rule forbids, so the orchestrator or the tech lead decides. Fallback with no exec: on Booking Price setup, filter next step = Add hotels & services, take a 2-day/1-night served tour, and check on Supply › Hotels that no active hotel sits at its overnight place.
2. **Supply › Pricing rules & FX (read only).** Confirm an approved b2b rule in force today with an RRP markup set (and pax bands present). If it is missing, the tech lead must be ready to act as second person on it, or the From $X part is dropped.
3. **CIS › Platform › Staff & access.** Confirm the business owner's Booking grant is `admin`. Confirm the shared content/booking mailbox account's Booking role (AA-1155 mismatch).
4. **Booking › Pricing policy › Staff sign-in.** Read "Administrators need an authenticator code". If Yes, she needs an authenticator ready, or admin actions return 403 `mfa_required`.
5. **SUP-000019 › Bank accounts (read only).** Check that no "contacts recently changed" warning is shown.
6. **ISMS.** Decide which document she reads (link) and where the approval date is recorded. Have it open on screen.
7. **Runbook fixes.** Update items 1 to 9 of section 2 at least.

## 4. Open asks from the business owner (Jira) to cover

She has written no Jira comment since 20/11. Her asks are in the descriptions of three tasks she created, all in Backlog.

- **PR-31 Price system** (23/11), the main one:
  - Her example price table (20/01-31/03/2027; 2 pax 2190, 4 pax 1770, 5-7 pax 1745, 8 pax 1550 USD pp, twin share) was **never entered on Dev**. Our 24/11 comment says so. Offer to enter it with way 1. Ask which tour it belongs to.
  - Her bands are 1, 2, 4, 5-7, 8-10. The system uses 1, 2, 3, 4, 5-7, 8-10, 11+ and "on request from 9". Ask whether 9-10 should stay instant (a two-person Pricing policy change).
  - Several suppliers per trip and 1-year supplier prices with an expiry reminder: confirm what exists and what does not.
  - Correct one point if she asks: per the tickets lane, our comment 10690 says an approved manual version "wins in the tariff". The code shows the agency tariff and quotes always price components at supplier rates (`tariff.py:24-27`). A hand version only sets the public From/RRP price and the tariff's season and band windows. Re-read 10690 before the meeting.
- **PR-30 Hotel data**: answered. The Excel re-import diff is not yet run live on Dev.
- **PR-29 Optional activities**: answered. The add-on limit in a CRM quote has not been tried by hand.
- **Claims not proven live** (say so plainly if asked, do not demo):
  - the PR-26 calendar connect (Google consent scope pending, AA-1011);
  - the PR-30 re-import;
  - the PR-29 add-on limit;
  - her PR-31 table.

## 5. Still unverified (not checked live)

- Demo tour candidates, the b2b rule in force, its RRP markup and the live pax bands. The finder script was not run.
- The business owner's Booking grant; the `staff_admin_mfa_required` value; the shared mailbox account's Booking role.
- SUP-000019 contact changes in the last 30 days.
- Whether an inactive supplier named "SYNTHETIC price test" already exists (5 inactive SYNTHETIC suppliers, names not listed). The unique name in section 2 item 6 avoids this either way.
- Self-approval table row 2: "phí huỷ" and "allotment" as strictly two-person were not traced in code (pricing rules, FX, tiers, rate cards, stop-sales were).
- Controls seen only in source, not on screen, because the E2E accounts cannot reach them without a write:
  - Make business owner;
  - bank Approve;
  - View as;
  - Add rate;
  - Accept / Reject on Hotels & services;
  - Save draft / Submit for approval / Approve on versions.
- Timing claims (CRM 60 s, TripPlanner ~30 min, Content studio instant, the auto recompute within ~15 min) come from code, not from a live run.
- The UI was checked at 1440 px light only (no mobile or dark), signed in as the E2E accounts, not as the business owner.
- Whether CIS builds overnight destinations for a hand-made tour (only matters if the SYNTHETIC draft tour is used later).
- Whether Jira comment 10690 says what the tickets lane paraphrased.
- Claude Meetings entry for 11:00: not checked (missing projects:read permission).
