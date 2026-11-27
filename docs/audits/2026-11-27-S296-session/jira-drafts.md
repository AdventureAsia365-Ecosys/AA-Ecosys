# S296 — Jira drafts (Vietnamese, for the business owner)

Status: **DRAFT, not posted.** Waiting for the tech lead's approval ("Jira đăng").
Drafted 27/11/2026 ~20:45 +07. All numbers are from today's live checks on Dev (times per section).
Post each as a new comment with `contentFormat: html`; upload images with `uploadAttachmentToJiraIssue` (one call per
file) and embed them with `inlineFileId` / `inlineFileCollection` / `inlineFileName`, in the order listed. Do not change
any status.

Images ready to attach (cropped / renamed, Vietnamese without diacritics):
`/home/nghiep/projects/AA-Ecosys/.tmp-session/S296/jira-images/` (originals stay in `.tmp-session/S296/verify/`).

## Jira read before drafting (27/11, ~20:35 +07)

- Open issues `project in (PR, KAN, CON) AND statusCategory != Done`: read. Most recent: CON-40 (13:24), PR-23 (S295
  comment 10711, 12:47), PR-27/26/22 (26/11 06:22), PR-29, PR-24, PR-30, PR-25 (25/11 18:14), PR-31 (24/11).
- Last comments read so nothing repeats:
  - PR-26: 10709 (26/11, calendar sync), 10696 (24/11, planner inquiry, AA add-on, price display), 10684 (21/11).
    The "AA prices" page itself was first reported 06/11; today's change is the new columns, On request, terms panel, Money menu.
  - PR-25: 10699 (25/11, Suppliers labels), 10692 (24/11), 10688 (23/11, approval rules, group size bands).
    The Booking "My work" strip was first reported 20/11; today's change is the order, new approval tiles, folding, price setup card.
  - PR-22: 10708 (26/11, Product map, mobile workspace), 10704, 10697 (24/11, manual tour). CIS "My work" for content
    staff was reported 20/11 ("Quản trị viên vẫn vào trang Overview như cũ"); today: everyone lands there, approval tiles.
  - PR-23: 10711 (27/11 S295, supplier data protection; said "Tour chưa có giá ... sẽ không hiện giá").
  - PR-31: 10698 (24/11), 10690 (23/11) — the business owner's own "Price system" task.
  - PR-20: kỳ 6 = 10687, posted Mon 23/11 06:50, covers 17–23/11.

## Targets

| # | Issue | Post? | Content |
|---|---|---|---|
| 1 | PR-26 CRM cho đại lý | Yes | AA prices: twin share, single, child, infant, RRP; On request 8–10 / 11+; "Priced tours 2 of 844"; Money menu; booking conditions panel |
| 2 | PR-25 Booking | Yes | My work leads the dashboard, new approval tiles, folded empty queues, price setup progress; Meal plan column; tariff to agencies in twin share + single |
| 3 | PR-22 CIS | Yes | Everyone lands on My work; approval tiles; tiles open the filtered list; upload with another provider goes to Dup Review |
| 4 | PR-23 Portal tenant | Yes (short) | Corrects today's S295 line: "In my catalog" now says "Price on request" instead of hiding the price |
| 5 | PR-31 Price system (her task) | Optional | Two lines: agencies now see prices in her "per person, double occupancy" shape; points to PR-26 |
| — | PR-20 weekly report | **No** | Not due: kỳ 6 posted Mon 23/11; kỳ 7 (24–30/11) is due Sun 29/11 / Mon 30/11 (cadence rule S253). Carry-over notes at the end |
| — | PR-24, PR-27, KAN, CON | No | Nothing product-facing shipped for TripPlanner in this list; security.txt / infra / secrets / deploy fixes are not reported (tech-lead topics). KAN/CON never |

---

## 1. PR-26 — CRM cho đại lý

- **Why:** the agency-facing "AA prices" page changed shape (market pricing: twin share + single supplement), got the
  On request bands and the AA booking conditions panel. Shipped and checked live today.
- **Where:** new comment on PR-26.
- **Live check:** 27/11 ~20:15 +07, Dev, agency web `portal.` host, signed in as the owner of the test agency
  "Lữ hành Sen Vàng" (synthetic), 1440 and 390 px, light and dark. Read only.

**Comment (HTML, exactly as posted):**

```html
<p><span data-type="mention" data-user-id="70121:5793bdd5-44b1-4623-97d4-43c35d440869">@thule</span> Cập nhật CRM ngày 27/11 (Dev, đại lý thử Sen Vàng, tài khoản chủ đại lý thử):</p>
<p><strong>Trang AA prices</strong> (giá AA dành cho đại lý) làm lại theo cách báo giá thông dụng của thị trường:</p>
<ol>
<li><p><strong>Cột giá mới:</strong> với mỗi tour và mỗi bậc số khách, bảng có giá mỗi khách ở phòng đôi (twin share), phụ thu phòng đơn, giá trẻ em, giá em bé, mức giảm của đại lý và giá bán lẻ gợi ý (RRP) mỗi khách. Ví dụ tour &quot;Chiang Mai to Chiang Rai Mountain Cycling — 5 Days&quot;: 2 khách 337,67 USD, 4 khách 272,73 USD, 5–7 khách 259,75 USD mỗi khách ở phòng đôi; phụ thu phòng đơn 207,79 USD; giá bán lẻ gợi ý cho 2 khách 425 USD mỗi khách.</p></li>
<li><p><strong>Đoàn lớn báo giá theo yêu cầu:</strong> bậc 8–10 và 11+ khách ghi &quot;On request&quot; (đoàn từ 9 khách AA báo giá riêng), kèm một số tham khảo ghi &quot;Guide&quot;. Các bậc 1, 2, 3, 4, 5–7 hiện giá bình thường.</p></li>
<li><p><strong>Đầu trang ghi rõ</strong> ngày tính giá, mức giá của đại lý và số tour đã có giá: hôm nay &quot;Priced tours: 2 of 844&quot; (trên Dev mới có 2 tour có giá nhà cung cấp).</p></li>
<li><p><strong>Khung &quot;Booking conditions with AA&quot;</strong> ngay dưới bảng giá, áp cho mọi tour AA trừ khi tour hoặc đại lý có điều khoản riêng:</p>
<ul>
<li><p>Thanh toán: cọc 30 % khi booking được xác nhận; phần còn lại xuất hoá đơn 30 ngày trước khởi hành (đặt sát ngày thì thu đủ một lần); hoá đơn đến hạn sau 14 ngày.</p></li>
<li><p>Phí huỷ theo số ngày trước khởi hành: từ 31 ngày 0 %, từ 22 ngày 10 %, từ 15 ngày 25 %, từ 8 ngày 50 %, từ 2 ngày 75 %, dưới 2 ngày 100 % tổng booking.</p></li>
<li><p>Báo giá giữ giá 14 ngày; đoàn từ 9 khách báo giá theo yêu cầu; trẻ em tới 11 tuổi, em bé tới 1 tuổi (tour có thể đặt độ tuổi riêng).</p></li>
</ul></li>
<li><p><strong>Vị trí trong menu:</strong> AA prices nay nằm trong nhóm Money, cạnh Payments, Bookings, Bookings with AA, Commissions.</p></li>
<li><p>Đại lý không thấy tên nhà cung cấp hay giá gốc AA mua vào: đã quét toàn bộ chữ trên trang, không có.</p></li>
</ol>
<p>Đã thử 27/11 trên máy tính và điện thoại, nền sáng và tối: trang mở bình thường, đúng các cột, nhãn &quot;On request&quot; nằm đúng 4 dòng 8–10 và 11+ của 2 tour có giá. Còn một chỗ giao diện: trên màn hình máy tính cột tên tour đang quá hẹp nên tên bị ngắt dòng; sẽ chỉnh. Trên điện thoại hiển thị đúng (ảnh 1–2).</p>
<p>Ảnh theo thứ tự: (1) trang AA prices trên điện thoại, (2) bậc 8–10 và 11+ ghi &quot;On request&quot;, (3) khung &quot;Booking conditions with AA&quot;, (4) AA prices trong nhóm Money của menu.</p>
```

**Images (attach in this order):**

1. `.tmp-session/S296/jira-images/pr26-1-gia-aa-bang-gia.png` (crop of `verify/AA-1188/recheck/crm-aa-prices-390-light.png`, red mailbox banner cut off)
2. `.tmp-session/S296/jira-images/pr26-2-gia-aa-theo-yeu-cau.png` (crop of the same file, the 8–10 and 11+ cards)
3. `.tmp-session/S296/jira-images/pr26-3-dieu-kien-dat-tour-voi-aa.png` (= `recheck/crm-aa-terms-1440-light.png`)
4. `.tmp-session/S296/jira-images/pr26-4-menu-money-aa-prices.png` (= `recheck/crm-sidebar-money-1440-light.png`)

The 1440 full-page shot is not attached on purpose: the Tour column is ~40 px wide (finding N1), names break per syllable.

| Claim | Evidence |
|---|---|
| Columns twin share, single, child, infant, discount, RRP | `verify/AA-1188/evidence.md` recheck R2 (headers read from DOM, 14 rows; 390 cards same labels); skeptic confirmed on PNGs |
| Chiang Mai numbers 337,67 / 272,73 / 259,75 / 207,79; RRP 2 pax 425 | `verify/AA-1188/crm-bff-aa-tariff-usd.json` (27/11), same values on `recheck/crm-aa-prices-1440-light.png`; RRP 425 also on studio drawer |
| On request on 8–10 and 11+ only, with "Guide" amount; groups from 9 quoted on request | R3 (4 badges: Bohol + Chiang Mai × 8–10, 11+); JSON `group_on_request_min_pax 9`, `availability on_request` |
| "Priced tours: 2 of 844" | R4 `tariff-meta`; JSON `tours_priced 2`, `catalog_tours 844` |
| Booking conditions panel content | R5 + `recheck/crm-aa-terms-1440-light.png` (read today); CRM API log `GET /crm/v1/aa/terms 200` ×8 |
| AA prices under Money | R6 + `crm-sidebar-money-1440-light.png` |
| No supplier name / net / cost text | R7 regex over page text, 8 loads, 0 hits |
| Desktop Tour column too narrow; mobile fine | Recheck finding N1; R9 390 no overflow |

---

## 2. PR-25 — Booking

- **Why:** the Booking home page changed for every staff person (My work first, new approval tiles, price setup
  progress); the price workbook keeps meal plans; the tariff Booking sends to agencies is now twin share + single.
- **Where:** new comment on PR-25.
- **Live check:** 27/11, Dev, `booking.` admin. First run 18:33–18:47 +07, recheck 20:05–20:25 +07 after the follow-up
  fix; E2E accounts: admin and a "Product & operations" (contracting) account. Nothing approved or changed.

**Comment (HTML, exactly as posted):**

```html
<p><span data-type="mention" data-user-id="70121:5793bdd5-44b1-4623-97d4-43c35d440869">@thule</span> Cập nhật Booking ngày 27/11 (Dev):</p>
<ol>
<li><p><strong>Trang chủ mở đầu bằng My work</strong> cho mọi nhân viên:</p>
<ul>
<li><p>Nhóm &quot;To approve or pay&quot; (việc cần duyệt hoặc chi) đứng trước, rồi tới &quot;To do&quot;.</p></li>
<li><p>Thêm 4 ô duyệt: phiên bản giá, add-on, thay đổi mùa giá, ngày lễ chờ duyệt. Mỗi người chỉ thấy ô theo quyền của mình.</p></li>
<li><p>Hàng đợi đang trống gom vào một dòng &quot;Nothing waiting in N queues&quot;, bấm để mở ra.</p></li>
<li><p>Bấm một ô là mở đúng danh sách đã lọc, số trên danh sách khớp số trên ô. Đã thử 27/11: &quot;Trip checks overdue: no owner&quot; 23 → danh sách 23; &quot;Supplier bills to pay&quot; 2 → danh sách 2; &quot;Contracts ending soon&quot; 2 → 2 hợp đồng.</p></li>
<li><p>Người không làm bán hàng thấy phần Sales overview thu gọn.</p></li>
</ul></li>
<li><p><strong>Thẻ &quot;Price setup progress&quot;</strong> trên trang chủ: hôm nay &quot;2 of 844 tours ready to buy&quot;; 841 tour còn thiếu khách sạn và dịch vụ, 1 tour chỉ còn bước mở bán. Bấm số nào thì mở trang Price setup đúng bước đó (841 → 841 tour, 1 → 1 tour).</p></li>
<li><p><strong>File Excel giá (Price setup › Download workbook):</strong> sheet Components có thêm cột &quot;Meal plan&quot; (RO, BB, HB, FB, AI) cho từng đêm khách sạn. Tải file lên lại mà để trống ô này thì bữa ăn đã đặt của đêm đó được giữ nguyên; trước đây HB hoặc FB bị đổi về BB. Đã tải file 27/11 và thấy cột mới cùng dòng hướng dẫn ở sheet &quot;Read me&quot;. Phần tải lên lại đã kiểm bằng test tự động, chưa thử thật trên Dev vì tài khoản thử chỉ được xem.</p></li>
<li><p><strong>Bảng giá Booking gửi cho đại lý</strong> nay tính theo giá mỗi khách ở phòng đôi kèm phụ thu phòng đơn; bậc 8–10 và 11+ ghi &quot;On request&quot;. Đại lý xem ở trang AA prices trong CRM (chi tiết ở PR-26). Đã kiểm 27/11 qua CRM: 14/14 dòng giá của 2 tour có giá đều có đủ hai số này.</p></li>
</ol>
<p>Đã thử 27/11 bằng tài khoản thử quản trị viên và tài khoản thử vai trò &quot;Product &amp; operations&quot;, trên máy tính và điện thoại; không duyệt hay sửa gì. 4 ô duyệt mới đang là 0 trên Dev nên nằm trong dòng gom; chưa có việc chờ duyệt thật để bấm thử, trừ ô phiên bản giá (mở trang Price setup, 0 phiên bản chờ duyệt).</p>
<p>Ảnh: trang chủ Booking với My work, dòng &quot;Nothing waiting in 15 queues&quot; và thẻ Price setup progress.</p>
```

**Images (attach in this order):**

1. `.tmp-session/S296/jira-images/pr25-1-booking-trang-chu-my-work.png` (= `verify/AA-1190/recheck/booking-dashboard-1440-light.png`)

| Claim | Evidence |
|---|---|
| My work first, approve band first, 4 new tiles, "Nothing waiting in N queues" | `verify/AA-1190/evidence.md` items 7, 8 (`booking-my-work-summary.json`: `price_versions_to_approve`, `addons_to_publish`, `season_changes_to_approve`, `holiday_events_to_approve`); recheck PNG |
| Tile → filtered list 23 = 23, 2 = 2, contracts 2 | Item 11 + recheck R6 |
| Sales overview collapsed for non-sales role | Recheck R8 / item 13 (contracting account) |
| Price setup card 2 of 844, 841, 1; clicks match | Item 9 (`booking-price-setup.json`: add_components 841, make_sellable 1, done 2); recheck R5 (two lines) |
| Tested with admin + Product & operations accounts, nothing approved | Recheck R7/R8 + coverage table |
| Count-0 tiles not clicked live; price versions tile opened workbench "0" | Item 11 (price versions → "Price versions waiting for your approval: 0"); skeptic note "Tiles still not clicked live: count-0 tiles" |
| Meal plan column + Read me line in the downloaded workbook | `verify/AA-1187/evidence.md` items 1a (UI download + API, header row read), challenge re-unzip |
| Re-import keeps HB/FB: tests only | Item 1c: 403 `e2e_read_only`; Booking #337 integration test `test_reimport_keeps_a_hand_set_meal_plan` green |
| Tariff twin share + single, 14/14, On request 8–10 / 11+ | `verify/AA-1188/evidence.md` item 1 + `crm-bff-aa-tariff-usd.json` |

---

## 3. PR-22 — CIS nội dung & pipeline

- **Why:** CIS admin now opens on My work for every staff role (admins included, unlike 20/11), with approval tiles and
  filtered links; the tour upload no longer creates a second tour when only the provider differs.
- **Where:** new comment on PR-22.
- **Live check:** 27/11, Dev, CIS admin. First run ~18:35 +07, recheck 20:05–20:25 +07 after the tile-filter fix; E2E
  CIS admin and E2E content accounts. Nothing approved or changed. Upload fix: code + tests + deployed page text only.

**Comment (HTML, exactly as posted):**

```html
<p><span data-type="mention" data-user-id="70121:5793bdd5-44b1-4623-97d4-43c35d440869">@thule</span> Cập nhật CIS ngày 27/11 (Dev):</p>
<ol>
<li><p><strong>My work là trang đầu tiên của mọi nhân viên CIS</strong> khi đăng nhập, kể cả quản trị viên (trước đây quản trị viên vào trang Overview). Bấm logo cũng về My work.</p>
<ul>
<li><p>Ba nhóm: &quot;Needs your approval&quot;, &quot;Content work&quot;, &quot;Keep an eye on&quot;. Thêm 3 ô duyệt: cài đặt nền tảng chờ duyệt, ngoại lệ tuân thủ chờ duyệt, yêu cầu xoá dữ liệu chờ duyệt. Đề xuất của chính mình không hiện trong ô duyệt của mình khi cần người thứ hai duyệt.</p></li>
<li><p>Dòng tổng chỉ đếm việc cần làm (hôm nay &quot;44 items waiting in all&quot;). Tour giữ theo chính sách và thẻ địa điểm nằm riêng ở &quot;Keep an eye on&quot;, không cộng vào tổng.</p></li>
<li><p>Hàng đợi đang trống gom vào một dòng &quot;Nothing waiting in N queues&quot;.</p></li>
</ul></li>
<li><p><strong>Bấm một ô là mở đúng danh sách đã lọc</strong>, số khớp với ô. Đã thử 27/11: &quot;Review Queue: ready to review&quot; 25 → Review Queue lọc sẵn 25 tour; &quot;Held by policy&quot; 48 → 48; &quot;Supply copy: drafts to review&quot; 18 → 18; &quot;AA content: drafts&quot; 1 → 1; ô xoá dữ liệu mở đúng tab &quot;Tenant offboarding&quot;. Nút Back và Forward của trình duyệt giữ đúng bộ lọc.</p></li>
<li><p>Đã thử 27/11 bằng tài khoản thử quản trị viên và tài khoản thử nhân viên nội dung, trên máy tính và điện thoại; không duyệt hay sửa gì. 3 ô duyệt mới đang là 0 trên Dev nên chưa thấy một việc chờ duyệt thật đi qua.</p></li>
<li><p><strong>Tải file tour (Upload):</strong> một dòng có cùng tên và cùng nước với tour đã có nhưng khác nhà cung cấp không còn tạo ra tour thứ hai; dòng đó chuyển sang bước Dup Review để người xem quyết, và bản xem trước ghi rõ &quot;Same name and country, but another provider&quot;. Đã kiểm bằng test tự động và thấy câu thông báo mới trên trang Upload ở Dev; chưa tải thử một file thật vì tài khoản thử chỉ được xem.</p></li>
</ol>
<p>Ảnh theo thứ tự: (1) My work của quản trị viên, mở dòng các hàng đợi đang trống, (2) bấm ô &quot;Review Queue: ready to review&quot;: Review Queue lọc sẵn 25 tour.</p>
```

**Images (attach in this order):**

1. `.tmp-session/S296/jira-images/pr22-1-cis-my-work.png` (= `verify/AA-1190/cis-my-work-1440-light-expanded.png`, 18:35)
2. `.tmp-session/S296/jira-images/pr22-2-cis-o-review-queue-mo-dung-bo-loc.png` (= `verify/AA-1190/recheck/cis-review-tile-none-1440-light.png`)

| Claim | Evidence |
|---|---|
| Admin lands on `/admin/my-work`; logo → My work | `verify/AA-1190/evidence.md` item 1 |
| Content account lands on My work | Recheck R7 |
| Three bands, 3 approval tiles (settings, compliance exceptions, erasure); own proposals left out | Items 2, 5 + page text on `cis-my-work-1440-light-expanded.png` ("Your own proposals are left out while a second person must approve them") |
| Total 44; held by policy + place cards not counted | Items 2, 3 (`counts_toward_total: false`) |
| Tile clicks 25/48/18/1, erasure tab, Back/Forward | Item 6 (18, 1) + recheck R1–R4 (after CIS #1724) |
| Count-0 approval tiles not exercised with a real item | Item 5 (all 0); skeptic "tiles still not clicked live: count-0" |
| Upload: another provider → Dup Review, no new tour; tests + deployed text only | `verify/AA-1187/evidence.md` items 2a (403 read-only), 2b (string in deployed chunk), CIS #1720 tests green |

---

## 4. PR-23 — Portal tenant (Content studio)

- **Why:** this afternoon's S295 comment (10711) said tours without a Booking price "sẽ không hiện giá". Since #405 the
  card says "Price on request". Short correction so the posted text matches the live page.
- **Where:** new comment on PR-23.
- **Live check:** 27/11, Dev, `portal.` host, E2E studio viewer of test agency "Atlas & Hearth". Read only.

**Comment (HTML, exactly as posted):**

```html
<p><span data-type="mention" data-user-id="70121:5793bdd5-44b1-4623-97d4-43c35d440869">@thule</span> Bổ sung về giá trong Content studio (27/11, Dev, đại lý thử Atlas &amp; Hearth):</p>
<ul>
<li><p>Trang Marketplace › In my catalog: tour chưa có giá trong hệ thống đặt tour nay ghi &quot;Price on request&quot; thay vì để trống. Đã xem 27/11: 9/9 tour đại lý thử đã chọn đều ghi &quot;Price on request&quot; (trên Dev mới có 2/844 tour có giá).</p></li>
<li><p>Tour đã có giá hiện &quot;From $X per person&quot;, ghi rõ đây là giá bán lẻ gợi ý (RRP) cho 2 khách, không phải giá của đại lý. Đã thấy trên thẻ tour và trang chi tiết ở mục All tours: &quot;Chiang Mai to Chiang Rai Mountain Cycling&quot; From $425, tour Bohol From $110. Chưa thấy trong In my catalog vì đại lý thử chưa chọn tour nào có giá.</p></li>
</ul>
<p>Ảnh theo thứ tự: (1) In my catalog với &quot;Price on request&quot;, (2) trang chi tiết một tour có giá &quot;From $425 per person&quot;.</p>
```

**Images (attach in this order):**

1. `.tmp-session/S296/jira-images/pr23-1-in-my-catalog-price-on-request.png` (= `verify/AA-1188/studio-in-my-catalog-1440-light.png`)
2. `.tmp-session/S296/jira-images/pr23-2-tour-co-gia-from.png` (= `verify/AA-1188/studio-drawer-chiang-1440-light.png`)

| Claim | Evidence |
|---|---|
| 9/9 "Price on request", API `from_price` null | `verify/AA-1188/evidence.md` item 4a; recheck R10 |
| From $425 / $110 with RRP-for-2 note on All tours card + drawer | Item 4c; equals tariff 2-pax `rrp_per_person` |
| Priced tour inside "In my catalog" not seen | Item 4b / R10 NOT CHECKED (would need a write) |

---

## 5. PR-31 — Price system (her task) — OPTIONAL

- **Why:** her description asks for "Cost per person based on double occupancy" by group size (1, 2, 4, 5–7, 8–10). Today
  agencies see AA prices in exactly that shape. Post only if the tech lead wants her task to carry the link; the detail
  stays on PR-26.
- **Where:** new comment on PR-31.

**Comment (HTML, exactly as posted):**

```html
<p><span data-type="mention" data-user-id="70121:5793bdd5-44b1-4623-97d4-43c35d440869">@thule</span> Từ 27/11 (Dev), đại lý xem giá AA theo đúng dạng trong ví dụ của chị: giá mỗi khách ở phòng đôi theo bậc số khách (1, 2, 3, 4, 5–7), kèm phụ thu phòng đơn, giá trẻ em, em bé và giá bán lẻ gợi ý; bậc 8–10 và 11+ ghi &quot;On request&quot;. Chi tiết và ảnh ở PR-26.</p>
```

**Images:** none.

| Claim | Evidence |
|---|---|
| Twin share by band + single, child, infant, RRP; On request 8–10 / 11+ | Same as PR-26 rows (R2, R3, tariff JSON) |

---

## Carry-over for PR-20 kỳ 7 (24–30/11, due Sun 29/11 or Mon 30/11)

Not drafted today (cadence rule). Items from S296 to list in kỳ 7 once posted: CRM AA prices in twin share + booking
conditions (PR-26); My work landing + approval tiles in CIS and Booking (PR-22, PR-25); Meal plan column; upload with
another provider → Dup Review; studio "Price on request" (PR-23). Kỳ 6 "Kế hoạch tuần tới" rows to mark: "CIS: trang
soạn tour AA bằng tay gắn nhà cung cấp" (posted 24/11), "Booking: quy tắc duyệt cho đội 3 người … tách thành từng dịch
vụ" (posted 23–24/11). Numbers must be re-read on the day of the report.

## Posting log

| Issue | Comment id | Images | Posted at |
|---|---|---|---|
| PR-26 | — | — | not posted (waiting for approval) |
| PR-25 | — | — | not posted |
| PR-22 | — | — | not posted |
| PR-23 | — | — | not posted |
| PR-31 | — | — | optional, not posted |

## Posting log (27/11/2026, tech lead: "Đăng hết")

| Issue | Comment id | Images |
|---|---|---|
| PR-26 | 10712 | 4 inline |
| PR-25 | 10713 | 1 inline |
| PR-22 | 10714 | 2 inline |
| PR-23 | 10715 | 2 inline |
| PR-31 | 10716 | none |
