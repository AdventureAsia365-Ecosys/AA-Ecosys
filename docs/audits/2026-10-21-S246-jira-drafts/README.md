# S246: nháp Jira cuối phiên (21/10/2026)

Tác nhân: Claude Code. **Đã đăng 22/10/2026 sau khi Nghiệp duyệt cả 3: PR-19 comment 10488, PR-11 comment 10489 (bản sửa, chỉ phần CDN), PR-15 comment 10490.** Không đổi trạng thái, không tạo issue. Quy trình theo
`skill/aa-jira-update/SKILL.md`: nháp, Nghiệp duyệt nguyên văn, rồi mới đăng.

Quy tắc đã áp dụng:

- Tiếng Việt, câu ngắn, đứng tên Nghiệp (ngôi "em"), không nhắc agent, không mã Linear, không "ạ", không "như đã hứa".
  Không mở bằng "Dạ chị" (Nghiệp đã bỏ ở S243).
- Chỉ tag chị Thư, bằng mention node HTML (xem mục "Cách đăng").
- Chỉ ghi "chạy được" cho phần đã kiểm thật; phần chưa xong ghi "đang làm", không ghi ngày.
- Việc pháp lý và kinh doanh: giọng nhẹ, để chị Thư tự quyết, không hối.
- Bảng hỏi v2 cho chị Thư: coi như đã chốt, chưa gửi, **không** soạn gì.

## Phạm vi rà Jira (chỉ đọc, 21/10/2026 khoảng 17:30 +07)

- Đọc qua connector Atlassian (cloudId `78f9a2ea-f228-4ff6-b37d-7079434d2cef`): mọi issue PR, KAN, CON cập nhật trong
  21 ngày qua (51 issue), toàn bộ 27 issue của project PR (mô tả + epic cha), comment gần nhất của PR-11, PR-12,
  PR-13, PR-14, PR-15, PR-16, PR-17, PR-18, PR-19, PR-21, KAN-20.
- Tìm theo từ khoá (privacy, terms, legal, rate limit, CDN, CloudFront, pháp lý, điều khoản, map, bản đồ, quality,
  chất lượng): **không có** story nào về giới hạn tần suất, nhãn chi phí, trang Privacy/Terms hay gói pháp lý.
- Chị Thư có 1 comment chưa được trả lời: **PR-19** (20/10), nhờ dùng REA bóc tách Tern và TravelJoy. S245 Nghiệp chốt
  không trả lời trước khi xong thiết kế; nay thiết kế đã xong và được duyệt, nên nháp PR-19 trả lời luôn ý này.
- Comment cuối của PR-11, PR-12, PR-14, PR-15, PR-18 đều là của Nghiệp. Chị Thư không có câu hỏi mở nào khác.

## Tóm tắt

| # | Issue | Nội dung | Khuyến nghị |
|---|---|---|---|
| 1 | [PR-19](https://adventure-asia.atlassian.net/browse/PR-19) CRM cho travel agencies | Thiết kế cuối AA Partner + link trang + trả lời ý REA + mục 8 cần chị cho ý kiến | **Đăng** |
| 2 | [PR-11](https://adventure-asia.atlassian.net/browse/PR-11) Visual map planner | Ảnh phát qua CDN (đã nói sẽ làm ở comment 01/10); địa điểm dạng đường + gộp trùng ghi "đang làm" (S246 cuối: job vẽ đường chưa chạy, gộp trùng mới chạy thử không ghi) | **Đăng** |
| 3 | [PR-15](https://adventure-asia.atlassian.net/browse/PR-15) Dữ liệu tour thô / chạy lại nội dung | Kiểm số ngày, giữ bài khi bộ kiểm tra dữ kiện không chạy, bộ mẫu chặn bản sửa làm hỏng phần đã đạt | **Đăng** (hoặc chuyển sang epic PR-22, xem dưới) |
| – | [PR-20](https://adventure-asia.atlassian.net/browse/PR-20) báo cáo tuần | Chưa đến hạn (kỳ 1 PR-21 đăng 19/10; kỳ kế cho 20–26/10, soạn khoảng 26/10) | Không soạn; danh sách việc mang sang ở cuối file |
| – | [KAN-20](https://adventure-asia.atlassian.net/browse/KAN-20) Asian Trails | Thiết kế CRM chưa so với Asian Trails (chỉ bảng hỏi v2 có dẫn, mà bảng hỏi không được nhắc) | Không đăng bây giờ |

---

## 1. PR-19: CRM cho travel agencies (tenant) dùng với khách hàng của họ

- Link: <https://adventure-asia.atlassian.net/browse/PR-19> (story con của epic PR-26 "CRM cho đại lý"). Đăng thành
  comment mới.
- **Vì sao issue này:** đây là story CRM chị Thư tạo (kèm file spec trên Drive), và có comment 20/10 của chị đang chờ
  trả lời. Đăng ở story thay vì epic PR-26 để chị thấy ngay dưới comment của mình. Link trang thiết kế đi kèm comment
  này, không gửi lẻ qua Zalo.
- Nguồn nội dung: `docs/audits/2026-10-21-S246-crm-design-v3/final/brief-for-ms-thu.md` (mục 1, 3, 4, 5, 8). Chỉ hỏi
  đúng các mục ở mục 8, không thêm câu hỏi mới. Không nhắc luật sư trong comment (trong trang đã có, để chị tự tính).

### Nháp (HTML, `contentFormat: html`)

```html
<p><span data-type="mention" data-user-id="70121:5793bdd5-44b1-4623-97d4-43c35d440869">@thule</span> Cập nhật thiết kế CRM cho đại lý ngày 21/10/2026:</p>
<p>Bản thiết kế cuối đã xong, chị xem tại: <a href="https://claude.ai/artifact/2mCk7BrajpTpLEFao7PRt3">https://claude.ai/artifact/2mCk7BrajpTpLEFao7PRt3</a>. Trong trang có các màn hình mô phỏng và bản tóm tắt song ngữ Anh–Việt.</p>
<ul>
<li><p><strong>Sản phẩm:</strong> một ứng dụng web cho đại lý đối tác, tên tạm là AA Partner. Ứng dụng gộp các công cụ nội dung trên portal hiện nay với một CRM mới để đại lý quản lý bán hàng và chuyến đi của khách họ.</p></li>
<li><p><strong>8 màn hình chính:</strong> màn hình chính, pipeline, thư mục chuyến đi, công cụ soạn đề xuất theo từng ngày (tour AA có giá và tình trạng chỗ theo thời gian thực), trang đề xuất cho khách trên điện thoại, đồng ý và đặt cọc cùng cổng khách, thanh toán, báo cáo.</p></li>
<li><p><strong>Gộp với portal hiện tại:</strong> tháng 11/2026 công cụ nội dung chuyển sang ứng dụng mới ở phía sau, người dùng không thấy thay đổi. Khoảng tháng 12/2026 có một lần đăng nhập và một menu chung. Địa chỉ web giữ nguyên.</p></li>
<li><p><strong>Quyền riêng tư:</strong> dữ liệu khách thuộc về đại lý. AA chỉ thấy phần cần để vận hành chuyến có dịch vụ AA. Bộ phận hỗ trợ của AA chỉ xem được tài khoản khi chủ đại lý bật quyền.</p></li>
<li><p><strong>Tern và TravelJoy:</strong> em so sánh hai sản phẩm từ nguồn công khai (trang giới thiệu, trang giá, trang hướng dẫn, đánh giá của người dùng). Em không chạy REA vào ứng dụng của hai bên, vì điều khoản sử dụng của cả hai cấm dịch ngược và thu thập dữ liệu tự động. Những cách làm dễ dùng của hai bên đã đưa vào thiết kế.</p></li>
<li><p>Đây là bản thiết kế, chưa có màn hình nào chạy. Mọi tính năng sẽ được xây và thử trước với đại lý giả và dữ liệu giả.</p></li>
</ul>
<p>Những mục cần chị cho ý kiến (mục 8 trong bản tóm tắt), chị xem khi tiện:</p>
<ul>
<li><p>Pháp nhân ký hợp đồng đối tác, và điều khoản B2B hiện tại (công nợ, cọc, tiền tệ, phí thẻ).</p></li>
<li><p>Người phụ trách: nhập giá net; hỗ trợ đại lý thí điểm; quản lý lịch khởi hành và xác nhận tour theo yêu cầu; một quản lý (không phải kỹ sư) nhận báo động khi quyền truy cập khẩn cấp được dùng.</p></li>
<li><p>Hãng bảo hiểm: tên hãng và người liên hệ, để hỏi về mẫu giấy miễn trừ trách nhiệm cho tour trekking và việc chấp nhận chữ ký điện tử.</p></li>
<li><p>Nội dung từ đội kinh doanh: khoảng 10 gói "Trước khi đi", mẫu điều khoản và waiver song ngữ, video hướng dẫn ngắn, và giá net thật.</p></li>
<li><p>Về sau, khoảng tháng 2 đến tháng 3/2027: chọn 3 đến 5 đại lý thí điểm.</p></li>
</ul>
```

Bản đọc nhanh (cùng nội dung):

> @thule Cập nhật thiết kế CRM cho đại lý ngày 21/10/2026:
>
> Bản thiết kế cuối đã xong, chị xem tại: https://claude.ai/artifact/2mCk7BrajpTpLEFao7PRt3. Trong trang có các màn hình
> mô phỏng và bản tóm tắt song ngữ Anh–Việt.
>
> - **Sản phẩm:** một ứng dụng web cho đại lý đối tác, tên tạm là AA Partner. Ứng dụng gộp các công cụ nội dung trên
>   portal hiện nay với một CRM mới để đại lý quản lý bán hàng và chuyến đi của khách họ.
> - **8 màn hình chính:** màn hình chính, pipeline, thư mục chuyến đi, công cụ soạn đề xuất theo từng ngày (tour AA có
>   giá và tình trạng chỗ theo thời gian thực), trang đề xuất cho khách trên điện thoại, đồng ý và đặt cọc cùng cổng
>   khách, thanh toán, báo cáo.
> - **Gộp với portal hiện tại:** tháng 11/2026 công cụ nội dung chuyển sang ứng dụng mới ở phía sau, người dùng không
>   thấy thay đổi. Khoảng tháng 12/2026 có một lần đăng nhập và một menu chung. Địa chỉ web giữ nguyên.
> - **Quyền riêng tư:** dữ liệu khách thuộc về đại lý. AA chỉ thấy phần cần để vận hành chuyến có dịch vụ AA. Bộ phận
>   hỗ trợ của AA chỉ xem được tài khoản khi chủ đại lý bật quyền.
> - **Tern và TravelJoy:** em so sánh hai sản phẩm từ nguồn công khai (trang giới thiệu, trang giá, trang hướng dẫn,
>   đánh giá của người dùng). Em không chạy REA vào ứng dụng của hai bên, vì điều khoản sử dụng của cả hai cấm dịch
>   ngược và thu thập dữ liệu tự động. Những cách làm dễ dùng của hai bên đã đưa vào thiết kế.
> - Đây là bản thiết kế, chưa có màn hình nào chạy. Mọi tính năng sẽ được xây và thử trước với đại lý giả và dữ liệu
>   giả.
>
> Những mục cần chị cho ý kiến (mục 8 trong bản tóm tắt), chị xem khi tiện:
>
> - Pháp nhân ký hợp đồng đối tác, và điều khoản B2B hiện tại (công nợ, cọc, tiền tệ, phí thẻ).
> - Người phụ trách: nhập giá net; hỗ trợ đại lý thí điểm; quản lý lịch khởi hành và xác nhận tour theo yêu cầu; một
>   quản lý (không phải kỹ sư) nhận báo động khi quyền truy cập khẩn cấp được dùng.
> - Hãng bảo hiểm: tên hãng và người liên hệ, để hỏi về mẫu giấy miễn trừ trách nhiệm cho tour trekking và việc chấp
>   nhận chữ ký điện tử.
> - Nội dung từ đội kinh doanh: khoảng 10 gói "Trước khi đi", mẫu điều khoản và waiver song ngữ, video hướng dẫn ngắn,
>   và giá net thật.
> - Về sau, khoảng tháng 2 đến tháng 3/2027: chọn 3 đến 5 đại lý thí điểm.

### Bằng chứng (từng câu)

| Câu | Nguồn |
|---|---|
| Thiết kế cuối xong, Nghiệp duyệt | `.tmp-session/s246-decisions.md`: CRM v3 D1–D8 = a; bản cuối `docs/audits/2026-10-21-S246-crm-design-v3/final/` |
| Link trang, chia sẻ trong tổ chức | Nghiệp mở General access = Anyone at org (21/10, decisions log) |
| Sản phẩm, 8 màn hình, gộp portal, quyền riêng tư | `brief-for-ms-thu.md` mục 1, 3, 4, 5 |
| Tern/TravelJoy chỉ từ nguồn công khai, không chạy REA | `docs/audits/2026-10-20-S245-crm-tern-traveljoy/README.md` + `comparison.md` §6 (trích điều khoản) |
| Mục cần ý kiến | `brief-for-ms-thu.md` mục 8, không thêm gì |

### Lưu ý trước khi đăng

- Trang đang để quyền **Editor** cho cả tổ chức. Nếu chỉ muốn chị xem, Nghiệp có thể hạ xuống quyền xem hoặc bình luận.
- Nên tự mở link bằng một tài khoản khác trong tổ chức để chắc chị mở được.
- Không đính ảnh (trang đã có màn hình mô phỏng).

---

## 2. PR-11: Visual map planner

- Link: <https://adventure-asia.atlassian.net/browse/PR-11> (story con của epic PR-24 TripPlanner). Đăng thành comment
  mới.
- **Vì sao issue này:** comment 01/10 (10447) của Nghiệp ghi bước tiếp là "Đặt CloudFront (CDN của AWS) trước kho ảnh"
  vì ảnh đang phát qua server API bằng link tạm. Comment 15/10 (10469) ghi "Trip planner sẽ chuyển sang dùng nguồn mới"
  cho phần ghép địa điểm. Cả hai đều có tiến độ hôm nay.
- **Không đưa vào:** đồng bộ ảnh tự động mỗi ngày (bước 2 trong comment 01/10). Lịch đã dựng nhưng chưa có bằng chứng
  chạy 2 ngày liên tiếp, nên chưa báo.

### Nháp (HTML, `contentFormat: html`)

```html
<p><span data-type="mention" data-user-id="70121:5793bdd5-44b1-4623-97d4-43c35d440869">@thule</span> Cập nhật TripPlanner ngày 21/10/2026:</p>
<ul>
<li><p><strong>Ảnh tour qua CDN:</strong> ảnh giờ phát qua CDN tại img.lumiguides.it.com, không còn đi qua server bằng link tạm. Mỗi ảnh có link cố định và được lưu đệm gần người xem, nên server không phải tự phát từng ảnh. Đã kiểm trên bản đang chạy: ảnh trên trang TripPlanner được chuyển sang CDN, lần tải thứ hai lấy thẳng từ bộ nhớ đệm.</p></li>
<li><p>Việc chuyển TripPlanner sang dữ liệu địa điểm mới đang làm, gồm vẽ sông, đường mòn trekking và đường bộ thành đường kẻ trên bản đồ, và tự gộp các địa điểm bị trùng.</p></li>
</ul>
```

Bản đọc nhanh:

> @thule Cập nhật TripPlanner ngày 21/10/2026:
>
> - **Ảnh tour qua CDN:** ảnh giờ phát qua CDN tại img.lumiguides.it.com, không còn đi qua server bằng link tạm. Mỗi ảnh
>   có link cố định và được lưu đệm gần người xem, nên server không phải tự phát từng ảnh. Đã kiểm trên bản đang chạy:
>   ảnh trên trang TripPlanner được chuyển sang CDN, lần tải thứ hai lấy thẳng từ bộ nhớ đệm.
> - Việc chuyển TripPlanner sang dữ liệu địa điểm mới đang làm, gồm vẽ sông, đường mòn trekking và đường bộ thành đường
>   kẻ trên bản đồ, và tự gộp các địa điểm bị trùng.

### Bằng chứng (từng câu)

| Câu | Bằng chứng | Khi nào |
|---|---|---|
| Ảnh phát qua CDN | CIS #890 (`0151bb83`) + Infra #251 (`e90f7ab`) merged. Kiểm live: trang chủ `tripplanner.lumiguides.it.com` chứa link `api-cis…/content/photos/38570b4b…?size=small`; GET trả **302** tới `https://img.lumiguides.it.com/sri-lanka/…-600.webp?v=bde509793577`, `cache-control: public, max-age=86400` | 21/10 ~17:36 +07 (phiên này, curl) |
| Lần tải thứ hai từ bộ nhớ đệm | Cùng URL CDN: lần 1 `200 image/webp`, `x-cache: Miss from cloudfront`; lần 2 `200`, `x-cache: Hit from cloudfront` | 21/10 ~17:36 +07 |
| Chỗ lưu + trang quản trị địa điểm dạng đường, gộp trùng tự động | CIS #895 (`bea06563`, migration 253/255/256/257) + #896 (`8385f0db`); Infra #253 (bản sao migration); log apply `.tmp-session/s246-255…-apply.log`, `s246-256…`, `s246-257…` | 21/10 (S246) |
| Đang tắt với khách; chuyển nguồn đang làm | Theo phiên điều phối (TP #120 tp-017 id-map đã merge, chưa lật nguồn dữ liệu) | 21/10 (S246) |

### Lưu ý trước khi đăng

- **Sửa cuối S246:** bỏ hai câu "địa điểm dạng đường" và "gộp trùng tự động ... đã chạy trên hệ thống thử" — migration và code đã lên Dev nhưng job `place_shape` chưa chạy và job gộp trùng mới chạy plan-only (0 cặp gộp), nên chưa phải tính năng chạy được; gộp thành một câu "đang làm". Bỏ dòng ảnh (câu CDN đã có bằng chứng curl live).
- Theo quy tắc bằng chứng, câu về ảnh hiện mới có kiểm bằng curl. **Cần chụp 2 ảnh trước khi đăng**: (1) trang tour
  TripPlanner có ảnh (kèm tab Network thấy `img.lumiguides.it.com` nếu muốn), (2) tab Lines trên `/admin/places`. Nếu
  không có ảnh thì bỏ dòng "Ảnh:" và câu "Đã kiểm trên bản đang chạy" chỉ giữ phần đã curl.
- Ảnh trang admin: kiểm không lộ email nhân viên hay khoá.
- Trong nhánh AA-847 còn một ghi chú song ngữ về giấy phép dữ liệu bản đồ (ODbL) cho chị Thư. Nếu Nghiệp muốn gửi thì
  đưa vào báo cáo tuần sau khi nó được merge; nháp này không nhắc.

---

## 3. PR-15: Dữ liệu tour thô trước khi chạy lại toàn bộ nội dung

- Link: <https://adventure-asia.atlassian.net/browse/PR-15> (story con của epic PR-22 CIS). Đăng thành comment mới.
- **Vì sao issue này:** đây là story chị theo dõi chất lượng nội dung Master qua đợt chạy lại toàn bộ (12 comment,
  bảng số theo nước). Trong PR-22 không có story riêng nào về kiểm tra chất lượng. **Phương án khác:** đăng ở epic PR-22
  nếu Nghiệp muốn giữ PR-15 chỉ cho số liệu tour thô.
- Chỉ ghi đúng 3 việc đã có bằng chứng. Không nhắc model, Jev hay chi phí.

### Nháp (HTML, `contentFormat: html`)

```html
<p><span data-type="mention" data-user-id="70121:5793bdd5-44b1-4623-97d4-43c35d440869">@thule</span> Cập nhật kiểm tra chất lượng nội dung tour ngày 21/10/2026:</p>
<ul>
<li><p><strong>Kiểm số ngày:</strong> mỗi tour được viết lại giờ được tự kiểm số ngày trong lịch trình có khớp với thời lượng tour không. Phần kiểm này dùng luật cố định, không dùng AI, nên lần nào cũng cho cùng kết quả. Chạy trên 892 tour đã đăng, hệ thống tìm ra 79 tour có cấu trúc ngày chưa đúng, ví dụ một tour 3 giờ bị viết thành 4 ngày.</p></li>
<li><p><strong>Giữ bài khi bộ kiểm tra dữ kiện không chạy được:</strong> bài viết được giữ lại chờ duyệt thay vì tự đăng. Đã thử trên bản Dev.</p></li>
<li><p><strong>Sửa lỗi không làm hỏng phần đã đạt:</strong> khi hệ thống sửa một đoạn bị lỗi, phần đã qua kiểm tra không bị hỏng theo. Có một bộ mẫu kiểm tra tự động; thay đổi phần mềm nào làm hỏng phần đã đạt sẽ bị chặn trước khi lên hệ thống.</p></li>
</ul>
```

Bản đọc nhanh:

> @thule Cập nhật kiểm tra chất lượng nội dung tour ngày 21/10/2026:
>
> - **Kiểm số ngày:** mỗi tour được viết lại giờ được tự kiểm số ngày trong lịch trình có khớp với thời lượng tour
>   không. Phần kiểm này dùng luật cố định, không dùng AI, nên lần nào cũng cho cùng kết quả. Chạy trên 892 tour đã
>   đăng, hệ thống tìm ra 79 tour có cấu trúc ngày chưa đúng, ví dụ một tour 3 giờ bị viết thành 4 ngày.
> - **Giữ bài khi bộ kiểm tra dữ kiện không chạy được:** bài viết được giữ lại chờ duyệt thay vì tự đăng. Đã thử trên
>   bản Dev.
> - **Sửa lỗi không làm hỏng phần đã đạt:** khi hệ thống sửa một đoạn bị lỗi, phần đã qua kiểm tra không bị hỏng theo.
>   Có một bộ mẫu kiểm tra tự động; thay đổi phần mềm nào làm hỏng phần đã đạt sẽ bị chặn trước khi lên hệ thống.

### Bằng chứng (từng câu)

| Câu | Bằng chứng |
|---|---|
| Kiểm số ngày, luật cố định, 79/892 | CIS #893 (`8aaef159`, "one duration and day parser, S1 day oracle … in shadow"); số liệu theo phiên điều phối S246 (báo cáo `scripts/aa925/day_oracle_report.py`, ghi trong PR body #893) |
| Giữ bài khi bộ kiểm tra dữ kiện không chạy | CIS #894 (`a5f3da88`, "degraded detectors that hold"); drill `scripts/aa925/jev_drill.py` trên image đã deploy (Dev), theo phiên điều phối |
| Bộ mẫu chặn bản sửa làm hỏng phần đã đạt | CIS #891 (`66c8764e`, Q0 corpus + bước CI "red on base"); nhánh demo `test/aa-925-q0-demo-flip` đỏ ở Unit Tests |

### Lưu ý trước khi đăng

- Phần kiểm số ngày đang **chạy ở chế độ ghi lại** (shadow): nó kiểm và đếm, chưa tự chặn bài. Nháp chỉ nói "tự kiểm"
  và "tìm ra", không nói "chặn". Giữ đúng như vậy.
- Chị có thể hỏi 79 tour đó sẽ được xử lý thế nào. Nếu đã có kế hoạch, Nghiệp có thể thêm một dòng "Bước tiếp: …";
  nháp không tự hứa.
- Comment 30/09 ở PR-13 (Jev) có câu "khi Jev lỗi, bước đó giữ luật cũ". Với bộ kiểm tra dữ kiện, hành vi nay đổi thành
  giữ bài chờ duyệt. Nháp này không nhắc Jev; Nghiệp cân nhắc có cần nói ở PR-13 không (khuyến nghị: không, để báo cáo
  tuần nếu cần).

---

## Không đăng bây giờ

| Issue | Lý do |
|---|---|
| [PR-20](https://adventure-asia.atlassian.net/browse/PR-20) báo cáo tuần | Kỳ 1 ([PR-21](https://adventure-asia.atlassian.net/browse/PR-21), 01–19/10) đăng 19/10. Từ S245 báo cáo là hằng tuần, kỳ kế cho 20–26/10, soạn khoảng 26/10. Báo cáo là một Story mới dưới PR-20: chỉ tạo khi Nghiệp duyệt lúc đó. Danh sách mang sang ở dưới |
| [KAN-20](https://adventure-asia.atlassian.net/browse/KAN-20) Asian Trails | Comment 01/10 của Nghiệp hẹn cập nhật "khi thiết kế giá và đặt chỗ B2B cho đại lý". Thiết kế CRM có phần tour AA giá net B2B trong đề xuất, nhưng bản thiết kế cuối **không** so với Asian Trails; chỉ bảng hỏi v2 có dẫn, mà bảng hỏi không được nhắc. Đề xuất: cập nhật KAN-20 khi làm phần tour AA trong đề xuất (dự kiến tháng 1/2027), bằng tiếng Anh như luồng hiện tại |
| [PR-26](https://adventure-asia.atlassian.net/browse/PR-26) epic CRM | Đăng ở story PR-19. Phần lộ trình trong mô tả epic cập nhật lúc báo cáo tuần, không phải bây giờ |
| [PR-27](https://adventure-asia.atlassian.net/browse/PR-27) epic Nền tảng, [PR-14](https://adventure-asia.atlassian.net/browse/PR-14) đăng nhập | Giới hạn tần suất, header bảo mật, nhãn chi phí không có story riêng; giới hạn đăng nhập sai không phải tính năng đăng nhập không mật khẩu. Đưa vào báo cáo tuần |
| [PR-12](https://adventure-asia.atlassian.net/browse/PR-12) Booking, [PR-18](https://adventure-asia.atlassian.net/browse/PR-18) portal | Việc hôm nay ở hai app này là việc phía sau (khoá trang tài liệu API Booking, giới hạn đăng nhập portal, gắn nhãn dữ liệu cá nhân). Đưa vào báo cáo tuần |
| [PR-13](https://adventure-asia.atlassian.net/browse/PR-13), [PR-16](https://adventure-asia.atlassian.net/browse/PR-16), [PR-17](https://adventure-asia.atlassian.net/browse/PR-17), [PR-7](https://adventure-asia.atlassian.net/browse/PR-7) | Không có tính năng mới ship hôm nay trong phạm vi đã xác minh |
| Bảng hỏi v2 cho chị Thư | Đã chốt, chưa gửi, Nghiệp tự trao đổi. Không soạn |
| KAN-\*, CON-\* còn lại | Không liên quan việc kỹ thuật hôm nay |

## Mang sang báo cáo tuần kỳ kế (20–26/10)

Ghi sẵn để soạn khoảng 26/10. Đều là việc chưa có story Jira riêng:

- Giới hạn tần suất cho các điểm truy cập công khai của cả 3 app: giới hạn số lần đăng nhập sai (admin, tenant), giới
  hạn tần suất ở cổng API (đăng nhập 20/40, nội dung 300/600, mặc định 50/100). Chi phí thêm khoảng 0 USD/tháng.
- Header bảo mật cho trang admin, portal và TripPlanner; trang tài liệu API của Booking chỉ mở cho admin.
- Nhãn chi phí: 86 tài nguyên AWS có nhãn, 0 tài nguyên thiếu nhãn (kỳ 1 đã báo "gắn nhãn chi phí theo từng ứng dụng",
  kỳ này báo kết quả phủ đủ). Số tiền: vẫn chờ rà soát chi phí đầu tháng 11.
- Ảnh qua CDN: đã báo ở PR-11, báo cáo chỉ ghi "Đã báo ở PR-11".
- Gắn nhãn dữ liệu cá nhân cho các cột của Booking và TripPlanner (sổ quản lý dữ liệu cá nhân).
- **Điểm để chị lưu ý (giọng nhẹ):** trang Privacy và Terms cùng gói pháp lý đã có bản nháp để chị xem khi tiện; việc có
  cần luật sư hay không là chị quyết.

## Cách đăng (khi Nghiệp duyệt)

- Mention chị Thư: dùng `contentFormat: html` với
  `<span data-type="mention" data-user-id="70121:5793bdd5-44b1-4623-97d4-43c35d440869">@thule</span>`. Viết `@thule`
  dạng markdown sẽ không thành mention thật.
- Comment không ảnh (PR-19, PR-15): `addOrEditJiraIssueComment` (issue key, `contentFormat: html`, body = khối HTML).
- Comment có ảnh (PR-11): `executeWrite` `uploadAttachmentToJiraIssue` mỗi file một lần → chạy `uploadCommand`, lấy
  `data.id` + `collection` → `addOrEditJiraIssueComment` với `inlineFileId`, `inlineFileCollection`, `inlineFileName`
  (tên file tiếng Việt không dấu, ví dụ `anh-tour-qua-cdn.png`, `dia-diem-dang-duong.png`). Không attach riêng thêm lần
  nữa.
- Sau khi đăng: ghi comment id vào session block S246.
