# S285 — Jira drafts

Status: PR-30 posted 19/11 after the tech lead's approval (comment 10672, https://adventure-asia.atlassian.net/browse/PR-30?focusedCommentId=10672). The Zalo message is sent by the tech lead.

## PR-30 "Khach san" — comment (reply to "check trên data set đã có table data của khách sạn chưa?")

Posted as HTML (mention node for @thule). Text:

@thule Dạ chị,

Hệ thống đã có sẵn bảng dữ liệu khách sạn, nằm trong app Booking (mục Hotels và Suppliers của trang quản trị Booking). Hiện chưa nhập khách sạn thật nào: các dòng đang có trên môi trường Dev đều là dữ liệu giả lập để kiểm tra tính năng.

Các bảng và cột chính:

| Bảng | Dùng để | Cột chính |
|---|---|---|
| Nhà cung cấp (suppliers) | Công ty cung cấp dịch vụ (khách sạn, xe, hướng dẫn viên, vé tham quan, hoạt động…) | Mã SUP-xxxxxx, tên công ty, nhóm dịch vụ, website, người liên hệ (tên, chức danh, e-mail, điện thoại), địa chỉ, khu vực, quốc gia, ghi chú nội bộ, trạng thái |
| Khách sạn (hotels) | Thông tin khách sạn | Mã HTL-xxxxxx, nhà cung cấp, tên, kiểu khách sạn, hạng sao 1–5, địa chỉ, điểm đến, quốc gia, toạ độ, giờ nhận / trả phòng, tiện ích (tối đa 50), link (tối đa 10), ghi chú nội bộ, trạng thái (đang dùng / ngưng) |
| Loại phòng (hotel room types) | Các loại phòng của từng khách sạn | Khách sạn, tên loại phòng, số khách tối đa (1–20), loại giường, ghi chú, trạng thái |
| Hợp đồng nhà cung cấp (supplier contracts) | Hợp đồng giá theo năm / mùa | Tiêu đề, số tham chiếu, hiệu lực từ – đến, tiền tệ, điều khoản thanh toán, chính sách huỷ, trạng thái; một người soạn, người thứ hai duyệt mới có hiệu lực |
| Giá (supplier rates) | Giá net theo hợp đồng | Loại phòng (hoặc dịch vụ), mùa, hiệu lực từ – đến, đơn vị (đêm phòng), gói ăn (RO / BB / HB / FB / AI), số khách min – max, giá net, tiền tệ, ghi chú |
| Ảnh (media) | Ảnh khách sạn | File ảnh, kích thước, quyền sử dụng, trạng thái |
| Thành phần tour (trip plan components) | Gắn khách sạn vào từng đêm của tour | Tour, ngày thứ mấy, loại phòng (hoặc dịch vụ) |

Dữ liệu hiện có trên Dev (toàn bộ là dữ liệu giả lập để test, không phải khách sạn thật):

| Bảng | Số dòng | Ghi chú |
|---|---|---|
| Nhà cung cấp | 6 | Tên công ty thử nghiệm; 5 nhà cung cấp có nhóm khách sạn |
| Khách sạn | 5 | 4 đang dùng, 1 ngưng; 2 có hạng sao, chưa có toạ độ |
| Loại phòng | 5 | |
| Giá phòng | 7 | Đều USD; 6 dòng gói ăn sáng (BB) |
| Ảnh khách sạn | 2 | |

Cách nhập khi có dữ liệu thật:

- Khách sạn và loại phòng: tạo trên trang Hotels của Booking.
- Giá phòng: tải file Excel mẫu giá của nhà cung cấp, điền và tải lên; hệ thống kiểm từng dòng và báo lỗi theo sheet / dòng / cột trước khi ghi, rồi người thứ hai duyệt.
- Gắn khách sạn vào tour: hệ thống tự gợi ý khách sạn cho từng đêm dựa vào lịch trình tour, nhân viên chấp nhận hoặc đổi.

## Zalo — PR-29 and PR-30 (to Ms. Thư, plain text, for the tech lead to send)

Dạ chị,

Em có xem 2 việc chị mới giao trên Jira, em hỏi thêm cho rõ để làm đúng ý chị.

Việc "Optional activity add in":
Em hiểu là cho khách chọn thêm các hoạt động tuỳ chọn có tính tiền vào một tour, ví dụ tour Bali 7 ngày thì khách chọn thêm lặn biển hoặc spa, giá cộng vào báo giá. Hiện hệ thống đã có danh mục dịch vụ / hoạt động của nhà cung cấp và nhân viên thêm được vào một booking bằng tay, nhưng chưa có danh sách hoạt động tuỳ chọn gắn sẵn cho từng tour để khách hoặc đại lý tự chọn.
Nhờ chị xác nhận giúp em mấy điểm:
Có phải ý chị là như trên không, hay là việc khác (ví dụ chỉ hiển thị hoạt động tuỳ chọn trong nội dung tour)?
Ai sẽ chọn thêm: khách trên trang TripPlanner, đại lý khi đặt tour, hay nhân viên AA khi làm báo giá?
Danh sách hoạt động tuỳ chọn của mỗi tour lấy từ đâu: trong file Excel tour hiện có đã có cột này chưa, hay AA sẽ nhập riêng?
Giá hoạt động tuỳ chọn tính theo người hay theo nhóm, có cần chọn ngày nào trong tour không?

Việc "Khách sạn":
Em đã trả lời trên Jira: hệ thống đã có bảng khách sạn, loại phòng, giá phòng theo hợp đồng, nhưng chưa có dữ liệu khách sạn thật, các dòng đang có chỉ là dữ liệu giả lập để test.
Nhờ chị cho em biết thêm:
Chị đang có sẵn danh sách khách sạn (file Excel hay hợp đồng với nhà cung cấp) để nhập vào không? Nếu có chị gửi em 1 file mẫu, em làm chức năng nhập hàng loạt theo đúng file đó.
Chị cần dữ liệu khách sạn để làm gì trước: báo giá tour, hiển thị khách sạn trong nội dung tour cho khách xem, hay cả hai?

## Round 2 drafts (19/11) — approved by the tech lead and posted: PR-29 comment 10673, PR-30 comment 10674

### PR-29 "Optional activity add in" — comment

@thule Dạ chị,

Em đã chốt cách làm phần hoạt động tuỳ chọn theo ý chị: mọi hoạt động đều do nhà cung cấp của AA phục vụ, dữ liệu là của AA, đại lý chỉ chọn và báo giá chứ không tự thêm hay sửa hoạt động.

Cách hoạt động:

| Phần | Cách làm |
|---|---|
| Gắn với tour | Hoạt động gắn theo địa điểm. Mỗi ngày của tour hiện các hoạt động ở nơi khách ngủ đêm đó trước, rồi tới các nơi đi qua trong ngày |
| Ai nhập | Nhân viên content của AA nhập hoạt động và nội dung (tên, mô tả, ảnh); nhân viên hợp đồng nhập giá net của nhà cung cấp; một người thứ hai duyệt rồi mới bán |
| Giá còn hạn | Hoạt động chỉ hiện ở những ngày có giá còn hạn. Ví dụ hợp đồng 2026 hết hạn 31/12 mà hợp đồng 2027 chưa duyệt thì từ 01/01/2027 hoạt động tạm ẩn. Hệ thống báo trước 60 ngày khi hợp đồng sắp hết hạn |
| Giá trẻ em | Dùng đúng giá trẻ em nhà cung cấp ghi. Nhà cung cấp không ghi thì dùng tỉ lệ mặc định do bộ phận hợp đồng đặt; chưa đặt thì tính bằng giá người lớn để AA không bị lỗ |
| Còn chỗ | Mặc định hỏi lại nhà cung cấp trước khi xác nhận. Có hạn chót đặt, ngày và giờ hoạt động trong tuần, số khách tối thiểu, ngày dừng bán. Nhà cung cấp nào đồng ý xác nhận ngay hoặc giữ sẵn số chỗ thì ghi vào hợp đồng, hệ thống xác nhận ngay |
| Trang của đại lý | Hiện giá "từ X/khách", tính từ giá B2B của AA nhân hệ số giá đại lý tự đặt, làm tròn theo tiền tệ (ví dụ USD tròn tới 1 USD, VND tròn tới 10.000 đ) để không ra số lẻ. Đại lý tắt được phần hiện giá. Giá B2B của AA không bao giờ hiện cho khách |
| Khi khách chọn | Khách tick chọn hoạt động, yêu cầu gửi về đại lý kèm hoạt động đã chọn; đại lý báo giá trong CRM |

Thứ tự làm: phần giá và quy tắc bán làm trước, rồi phần nhập hoạt động, sau cùng là hiển thị trên trang TripPlanner và trong CRM. Em sẽ cập nhật tiếp khi từng phần chạy được trên Dev.

### PR-30 "Khách sạn" — comment

@thule Dạ chị,

Em bổ sung phần so sánh với tài liệu PRD của AAA/Quanskill và cách làm khách sạn sẽ áp dụng.

So với PRD: phần khách sạn đã làm đúng và đầy đủ hơn PRD. PRD chỉ có một bảng khách sạn đơn giản (tên, quốc gia, điểm đến, nhà cung cấp, link, ảnh, mô tả), không có loại phòng, giá, mùa hay hợp đồng. Hệ thống hiện có đủ các phần đó, kèm hợp đồng có người thứ hai duyệt và nhập bảng giá bằng Excel.

Cách làm sẽ áp dụng, theo cách phổ biến của các công ty lữ hành địa phương (DMC):

| Phần | Cách làm |
|---|---|
| Hợp đồng | Hợp đồng là giữa AA và nhà cung cấp của AA (DMC), không phải trực tiếp với khách sạn. Mọi giá lưu theo giá net. Nếu bảng giá của nhà cung cấp ghi "giá công bố + % hoa hồng" (ví dụ 70 USD, hoa hồng 20 %) thì hệ thống tự quy ra giá net (56 USD) và giữ lại hai số gốc để đối chiếu |
| Một khách sạn, nhiều nhà cung cấp | Một khách sạn có thể mua qua nhiều nhà cung cấp; hệ thống giữ một danh bạ khách sạn chung và chặn nhập trùng (cùng tên, cùng nơi, cùng toạ độ) |
| Ai nhập | Nhân viên hợp đồng nhập thông tin và giá theo bảng của nhà cung cấp, ghi nguồn và ngày xác nhận; nhân viên content viết mô tả và chọn ảnh. Thông tin sai thì sửa một chỗ, các app khác tự đọc theo |
| Gói ăn | Mặc định phòng kèm bữa sáng; tour hoặc báo giá được chọn thêm bữa tối hoặc ăn cả ngày (resort có gói trọn gói) |
| Phòng giữ sẵn | Hỗ trợ đủ 3 kiểu: hỏi lại nhà cung cấp, bán tự do trong giới hạn, và số phòng giữ sẵn có hạn trả phòng. Mặc định hỏi lại cho tới khi hợp đồng ghi rõ kiểu khác |
| Nhập dữ liệu | Có file Excel mẫu cho thông tin khách sạn, loại phòng và bảng giá. Hệ thống kiểm trước khi ghi, ví dụ giá có bữa tối mà rẻ hơn giá chỉ có bữa sáng, mùa bị hở ngày, hay giá tăng bất thường so với năm trước |
| Nhắc hạn | Hệ thống nhắc khi hợp đồng sắp hết hạn và khi thông tin khách sạn lâu chưa được nhà cung cấp xác nhận lại |

Mã khách sạn chuẩn ngành loại tính phí (GIATA) chưa cần mua vì AA đang nhập tay; hệ thống chừa sẵn chỗ để nối sau. Khi có file khách sạn thật từ nhà cung cấp, em nhập theo các mẫu trên.

## S285 evening drafts (pending approval)

Status: drafts only, nothing posted, no status changed. Read before drafting (19/11 ~22:00): the newest comments on PR-20, PR-22..PR-27 (latest: PR-22 10671, PR-24 10669, PR-25 10670 on 18/11; PR-26 10666 on 17/11; PR-27 10663 on 16/11; PR-23 10647 on 12/11; PR-20 10661 kỳ 5 on 15/11) and PR-29/PR-30 (10673/10674 today). Nothing below repeats them; the TripPlanner chat pause itself was already posted on PR-24 (18/11), so PR-24 only adds what is new.
When posting: `contentFormat: html`, `@thule` as the mention node (`data-user-id="70121:5793bdd5-44b1-4623-97d4-43c35d440869"`), markdown tables → HTML tables, screenshots uploaded and embedded in the listed order. Screenshot paths are relative to `docs/audits/2026-11-19-S285-session/`.
No PR-20 draft tonight: the weekly report kỳ 6 (17–23/11) is due at the end of the week.

### E1 — PR-23 (Content studio): tour edits keep AA's facts; AI-allowance message; monthly bill card

Why: three studio changes shipped and checked live on Dev today; PR-23's last comment is 12/11.

Text:

@thule Cập nhật Content studio ngày 19/11 (Dev, đại lý thử):

1. **Đại lý sửa bài tour nhưng không đổi được dữ kiện của AA:**
   - Đại lý vẫn sửa câu chữ tự do. Nếu lần sửa đổi số ngày, địa điểm, con số hoặc phần bao gồm / không bao gồm (ví dụ "bảy ngày" thành "mười ngày", hay thêm "đã gồm vé máy bay quốc tế") thì hệ thống từ chối và giải thích: chỉ câu chữ được đổi, dữ kiện lấy từ Adventure Asia. Lần sửa bị từ chối không ghi gì.
   - Khi đại lý lưu một phần (ví dụ chỉ đoạn tóm tắt), tên tour, phụ đề và dòng SEO riêng của đại lý được giữ nguyên, không bị thay bằng bản của AA.
   - Mục Facts của đại lý giờ chỉ nhận điều khoản đặt tour của đại lý (đặt cọc, thanh toán, huỷ). Giá, mùa, visa và các dữ kiện tour khác lấy từ AA.
   - Đã thử 19/11 trên tour Pikey Peak của đại lý thử: 2 lần sửa dữ kiện bị từ chối, sửa câu chữ lưu được; xong đã trả tour về nội dung ban đầu.
2. **Hết hạn mức AI trong tháng:** trang Tour của tôi hiện thông báo hạn mức viết bằng AI của gói đã dùng hết, ngày hạn mức được làm mới (1/12) và nút Nâng cấp gói; có cả tiếng Anh và tiếng Việt, trên máy tính và điện thoại. Đã thử bằng cách đặt hạn mức của đại lý thử về 0 rồi trả lại như cũ, không tốn tiền AI.
3. **Thẻ "Hoá đơn tháng này" trên trang tổng quan:** liệt kê từng gói và giảm giá, khớp báo giá. Ví dụ đại lý thử: Growth 349 + CRM Core 3 chỗ 57 + TripPlanner 49, giảm gộp gói 10 % (−45,50), cần trả 409,50 USD.

Ảnh theo thứ tự: (1) thông báo từ chối khi lần sửa đổi dữ kiện tour, (2) bài tour sau khi lưu phần sửa câu chữ, (3) trang Facts chỉ còn điều khoản đặt tour, (4) thông báo hết hạn mức AI trên trang Tour của tôi (tiếng Việt), (5) thẻ hoá đơn tháng này.

Screenshots:
1. `aa1144/studio-tour-fact-locked-1440.jpg`
2. `aa1144/recheck-step5-saved-1440.png`
3. `aa1144/studio-facts-1440.jpg`
4. `aa1126/quota-studio-rewrite-refused-vi-1440-light.png`
5. `aa1129-l18/studio-billing-card-vi-1440.png`

| Claim | Evidence |
|---|---|
| Fact edits refused (days, inclusions), nothing written | Linear AA-1144 live re-check 19/11 (422 fact_locked ×2, v6 stayed on top); `aa1144/recheck.json` |
| Partial save keeps agency's own name / subtitle / SEO | AA-1144 re-check step 5 (v8 equals v7's own values); `recheck-step5-saved-1440.png` |
| Facts form only booking terms | AA-1144 CIS check (D7: only booking_terms; price → 422); `studio-facts-1440.jpg` |
| Tour restored | AA-1144: v9 = copy of v6 |
| Quota message EN/VI, 1440/390, $0, overrides removed | AA-1126 comment 19/11; `aa1126/quota-studio-rewrite-refused-*` |
| Bill card 349 + 57 + 49 − 45.50 = 409.50 | AA-1129 Done comment (matches /api/tenant/v1/billing); `aa1129-l18/studio-billing-card-*` |

Note: the drawer header still shows the AA tour name instead of the agency's own (display only, data is right); not mentioned to Ms. Thư.

### E2 — PR-24 (TripPlanner): Trip planner page in the agency apps; agency told when the AI allowance runs out

Why: new agency-facing TripPlanner settings shipped and checked live today; the 18/11 comment covered lead delivery and the chat pause only.

Text:

@thule Cập nhật TripPlanner ngày 19/11 (Dev, đại lý thử):

1. **Trang "Trip planner" trong app của đại lý** (CRM: Cài đặt › Tiện ích bổ sung; Content studio: Tài khoản › Trip planner). Trên một trang, đại lý thấy và chỉnh:

| Phần | Đại lý làm được gì |
|---|---|
| Địa chỉ planner | Sao chép hoặc mở link trang lên lịch của mình |
| Nơi nhận khách | Đại lý có CRM: khách vào thẳng CRM. Không có CRM: chọn e-mail, webhook hoặc tạm không nhận |
| Giao diện và ngôn ngữ | Màu thương hiệu, màu chữ, ngôn ngữ mở trang; trang planner đổi theo trong khoảng 20 giây |
| Tháng này | Số phiên AI đã dùng trên hạn mức (ví dụ 0 / 300), số khách gửi yêu cầu trong tháng và 24 giờ qua |
| Khách gửi yêu cầu | Danh sách mới nhất, mỗi dòng ghi kênh và đã giao tới nơi hay chưa |
| Khoá ký webhook | Khoá chỉ hiện một lần lúc tạo, có nút sao chép; tải lại trang thì chỉ còn phiên bản và ngày tạo |

   - Đã thử 19/11: CRM của đại lý thử hiện 4 yêu cầu, cả 4 đã giao vào CRM. Ở Content studio, đổi nơi nhận, màu và ngôn ngữ thì trang planner của đại lý đổi theo; xong trả về như cũ.
   - Nhân viên biên tập của đại lý chỉ xem, không có nút lưu. E-mail nhận khách không hợp lệ bị từ chối và báo ngay dưới ô nhập.
   - Còn thiếu: chọn tiếng Việt hiện mới đổi ngôn ngữ của trang, phần chữ trên planner vẫn tiếng Anh; sẽ dịch ở bước sau.
2. **Đại lý được báo khi hết số phiên AI của tháng:** khi trợ lý lên lịch tạm dừng vì hết hạn mức (đã báo 18/11), đại lý nhận một thông báo trên chuông Content studio, mỗi tháng một lần, ghi rõ khách mới vẫn dùng được planner (chỉ không có lịch trình do AI viết) cho tới khi hạn mức làm mới ngày 1/12. Đã thử 19/11 trên đại lý thử, không tốn tiền AI, rồi trả hạn mức về như cũ.

Ảnh theo thứ tự: (1) trang Trip planner trong CRM của đại lý thử, (2) trang Trip planner trong Content studio (tiếng Việt) lúc vừa tạo khoá, khoá đã được che trong ảnh, (3) thông báo hết phiên AI trên chuông Content studio.

Screenshots:
1. `aa1139/live-crm-owner-rehearsal-after-scope-1440.png`
2. `aa1139/live-studio-key-shown-once-after-scope-1440.png`
3. `aa1126/quota-tripplanner-bell-1440-light.png`

Optional extra: `aa1139/live-crm-owner-rehearsal-after-scope-390.png` (phone).

| Claim | Evidence |
|---|---|
| CRM page: address, lead channel "NOW: CRM", look, usage 0 of 300, 4 leads DELIVERED, key state | Linear AA-1139 Done comment 19/11; screenshot 1 |
| Studio: change route / theme / locale, planner follows within 20 s, restored | AA-1139 (PUT 200, read-back, `lang=vi` + accent within 20 s) |
| Key shown once, after reload only version + date | AA-1139; `live-studio-key-shown-once-*`, `live-studio-key-after-reload-*` |
| Editor read-only; invalid lead e-mail refused under the field | AA-1139 (editor no Save; 422 lead_email_not_public) |
| Vietnamese copy on the planner not done | AA-1139 follow-up 1 |
| Bell notice once a month, $0, override removed | AA-1126 comment 11:07Z (`tenant_ai_sessions_notice` once; bell text); checklist 18:30 "override đã gỡ" |

### E3 — PR-25 (Booking): staff admin in Vietnamese

Why: the Booking staff admin now has an EN | VI switch; shipped and checked live today.

Text:

@thule Trang quản trị Booking cho nhân viên AA giờ có tiếng Việt (19/11, Dev):

- Nút EN | VI ở đầu trang; trên điện thoại chọn ở Cài đặt › Giao diện. Trang tải lại vẫn giữ tiếng Việt, không chớp tiếng Anh.
- Đã kiểm 10 trang ở cả hai thứ tiếng, trên máy tính và điện thoại: bảng điều khiển, hồ sơ chuyến đi và chi tiết, khách sạn, dịch vụ, nhà cung cấp, quy tắc giá, máy tính giá, nhân viên, cài đặt. Hạng sao, loại khách sạn, loại dịch vụ, vai trò nhân viên, trạng thái chuyến ("Trước khởi hành", "Chưa phân công") đều đã có tiếng Việt.
- Còn vài chữ nhỏ (tiêu đề tab trình duyệt, một khoảng trắng thiếu ở trang Cài đặt) sẽ sửa cùng đợt giao diện Booking tiếp theo.

Ảnh theo thứ tự: (1) bảng điều khiển bằng tiếng Việt, (2) chi tiết một hồ sơ chuyến đi, (3) bảng điều khiển trên điện thoại.

Screenshots:
1. `aa1128/recheck-dashboard.png`
2. `aa1128/recheck-case-detail.png`
3. `aa1128/dashboard-vi-390-light.png`

Do not attach `aa1128/recheck-hotels.png`, `hotels-*` or `pricing-rules-*`: their test data shows internal labels (synthetic names with issue ids, "tech lead S278").

| Claim | Evidence |
|---|---|
| EN/VI switch, cookie, no English flash, hidden < 480 px (Settings › Appearance) | Linear AA-1128 comment 19/11 06:49Z |
| 10 pages, EN + VI, 1440 + 390, 0 console errors | AA-1128 (same comment); `aa1128/*-vi-*` |
| ~15 leftover strings fixed and re-checked | AA-1128 Done comment 07:42Z (10/10 PASS); `aa1128/recheck-*` |
| Small leftovers | AA-1128 Done comment "left out of scope" |

### E4 — PR-26 (CRM): own lines limited, AA item names locked, AI-budget message, plainer CRM wording

Why: CRM changes shipped and checked live today; PR-26's last comment is 17/11.

Text:

@thule Cập nhật CRM đại lý ngày 19/11 (Dev, đại lý thử Sen Vàng):

1. **Dòng dịch vụ trong báo giá:**
   - Dòng do đại lý tự thêm chỉ còn 4 loại: vé máy bay, visa, bảo hiểm và phí. Khách sạn, xe, hướng dẫn viên, hoạt động đều là dịch vụ của AA.
   - Tên dịch vụ của AA trong báo giá không sửa được. Đại lý thêm được một dòng ghi chú riêng dưới dịch vụ đó.
   - Đã thử 19/11: đổi tên một dịch vụ AA bị từ chối, tên giữ nguyên; thêm rồi xoá ghi chú đều được.
2. **Hết ngân sách AI trong tháng:** trang Trợ lý AI báo ngân sách AI tháng này đã dùng hết, gợi ý tự viết câu trả lời tới tháng sau hoặc nâng cấp gói (tiếng Anh và tiếng Việt). Đã thử bằng cách đặt ngân sách của đại lý thử về 0 rồi trả lại, không tốn tiền AI.
3. **Chữ trong CRM dễ đọc hơn:**
   - Nhật ký truy cập ghi bằng câu thường, ví dụ "Chủ đại lý 2 đã xem danh sách thành viên"; đã quét 2.050 dòng, không còn mã kỹ thuật.
   - Bổ sung bản dịch tiếng Việt ở nhiều trang, form gửi yêu cầu mang thương hiệu đại lý (Anh/Việt), mục "Cần bạn xử lý" ở trang chủ, chuyến khởi hành ngày mai ghi "Khởi hành ngày mai".

Ảnh theo thứ tự: (1) dịch vụ AA trong báo giá với dòng ghi chú của đại lý (ghi chú thử), (2) thông báo hết ngân sách AI ở trang Trợ lý AI, (3) nhật ký truy cập bằng tiếng Việt.

Screenshots:
1. `aa1144/crm-builder-note-item-1440.jpg` (the test note reads "S285 check note"; crop or accept)
2. `aa1126/quota-crm-settings-ai-vi-1440-light.png`
3. `aa1129-l18/access-log-vi-1440.jpg`

| Claim | Evidence |
|---|---|
| Agency own lines only flight / visa / insurance / fee | Linear AA-1144 CRM comment 07:21Z (live DB check of the CHECK constraints; builder refusals shipped in Partner #359) |
| AA item rename refused, note add / clear works | AA-1144 CIS + CRM check 09:48Z (403 aa_title_read_only; note 200 shown at 1440/390; cleared 200) |
| AI budget message EN/VI, $0, overrides removed | AA-1126 comment 10:53Z; `aa1126/quota-crm-settings-ai*` |
| Access log plain sentences, 2,050 rows 0 hex ids | AA-1129 Done comment 09:15Z; `aa1129-l18/access-log-*` |
| Translations, branded inquiry form, "Needs you", "Starts tomorrow" | AA-1129 comments 01:39Z and 03:13Z; `aa1129/`, `aa1129-l10/` |

Not claimed: "Ask AA for extra nights" (shipped, not exercised in the UI); the client-page note (needs a published quote).

### E5 — PR-22 (CIS admin): admin pages fit phones

Why: small but visible; optional, could also be folded into the kỳ 6 weekly report instead of its own comment.

Text:

@thule Trang quản trị CIS dùng được trên điện thoại (19/11, Dev): đã sửa 5 chỗ bị tràn ngang ở màn hình 390 px (thẻ cài đặt nền tảng, trang Decisions, nhật ký duyệt của Tenant QA, ô tìm đại lý, hồ sơ app). Kiểm lại 12/12 chỗ ở nền sáng và tối: không còn trang nào phải kéo ngang.

Ảnh: (1) trang Cài đặt nền tảng trên điện thoại.

Screenshots:
1. `aa1127/live-390-settings-cis-spend-light.png`

| Claim | Evidence |
|---|---|
| 5 defects fixed, 12/12 PASS light + dark, 0 px overflow | Linear AA-1127 comment 10:53Z (CIS #1604 deployed); `aa1127/live-390-*` |

### Left out on purpose

- AI gateway Budgets (one budget per AI connection with per-app shares, the CRM copy sent and in step): it is about AI provider connections / accounts, i.e. platform infrastructure, and there is no screenshot in the audit folder (the Budgets page shot after "Send to CRM" is the tech lead's own). Evidence exists in Linear (audit row 10:23:16 UTC, CRM PUT 200, 8/8 in step) if the tech lead wants a line in the weekly report.
- Spend environment flip (dev hard caps vs prod alert-only): infrastructure policy, no product change to show.
- CRM AI draft replies moved to Claude Haiku: a model / vendor choice (tech decision); no screenshot in the audit folder (only the blind-comparison page and a live call in the CRM ledger, 0.000321 USD). Can go into the weekly report as one plain line if the tech lead wants.

### Posted (19/11/2026 ~23:20 +07, tech lead approved "đăng hết")

| Draft | Issue | Comment |
|---|---|---|
| E1 | PR-23 | https://adventure-asia.atlassian.net/browse/PR-23?focusedCommentId=10675 |
| E2 | PR-24 | https://adventure-asia.atlassian.net/browse/PR-24?focusedCommentId=10680 (first try 400: a table inside a list item; reposted with the table outside the list) |
| E3 | PR-25 | https://adventure-asia.atlassian.net/browse/PR-25?focusedCommentId=10677 |
| E4 | PR-26 | https://adventure-asia.atlassian.net/browse/PR-26?focusedCommentId=10678 |
| E5 | PR-22 | https://adventure-asia.atlassian.net/browse/PR-22?focusedCommentId=10679 |
