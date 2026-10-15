# S237 — Jira update drafts (NOT posted; Nghiệp approves each before posting)

Site `adventure-asia.atlassian.net`, cloudId `78f9a2ea-f228-4ff6-b37d-7079434d2cef`. Post with `contentFormat: html`;
the mention is `<span data-type="mention" data-user-id="70121:5793bdd5-44b1-4623-97d4-43c35d440869">@thule</span>`.
Figures are from S237 (14–15/10/2026) runs and live checks. Status: draft.

---

## PR-17 — Tenant viết lại tour đúng giọng thương hiệu của tenant (no comment yet)

```html
<p><span data-type="mention" data-user-id="70121:5793bdd5-44b1-4623-97d4-43c35d440869">@thule</span> Cập nhật viết lại tour cho tenant ngày 15/10/2026:</p>
<ul>
<li><p>Hệ thống giờ giữ bản viết tốt nhất, không còn trường hợp lưu bản kém hơn bản đã đạt. Khi một câu sai, chỉ sửa đúng câu đó thay vì viết lại cả bài.</p></li>
<li><p>Thông tin nền về địa điểm (lịch sử, độ cao, niên đại) được phép dùng; hoạt động, dịch vụ, giờ giấc mà tour gốc không có thì vẫn không được thêm.</p></li>
<li><p>Chạy lại 14 cặp tour × tenant: 0 bài phải viết lại toàn bộ, chi phí khoảng 0,08 USD mỗi bản (trước đây 0,27 USD).</p></li>
<li><p>Điểm giọng thương hiệu trung bình (thang 10, đạt từ 7): Atlas &amp; Hearth 7,0; Terra Family 7,5; Trail Pulse 7,3; WildKind 7,0.</p></li>
<li><p>Bước tiếp: em gửi chị vài bản của Trail Pulse và Atlas &amp; Hearth để chị đọc thử giọng văn.</p></li>
</ul>
```

## PR-12 — Booking system (last comment 14/10: foundation + first flow)

```html
<p><span data-type="mention" data-user-id="70121:5793bdd5-44b1-4623-97d4-43c35d440869">@thule</span> Cập nhật Booking ngày 15/10/2026:</p>
<ul>
<li><p>Đã xong đợt 2 trên môi trường thử nghiệm: danh sách nhà cung cấp và hợp đồng; khách sạn, loại phòng, dịch vụ (xe, hướng dẫn, vé, bữa ăn) kèm giá net theo hợp đồng.</p></li>
<li><p>Gói tour bán được: 892 tour từ hệ thống nội dung hiện sẵn trong Booking, nhân viên đánh dấu tour nào được bán và dùng làm khung khi tạo hồ sơ chuyến đi.</p></li>
<li><p>Tỷ giá và quy tắc giá cần 2 người: một người nhập, người thứ hai duyệt; người nhập không tự duyệt được. Đã thử thật: nhập EUR 0,92/USD, anh Nghiệp duyệt, báo giá 1.000 USD giá net ra 1.410 EUR.</p></li>
<li><p>Lỗi thứ tự các chặng trong yêu cầu gửi từ TripPlanner đã sửa xong.</p></li>
<li><p>Booking đã có địa chỉ riêng: api-booking.lumiguides.it.com.</p></li>
<li><p>Bước tiếp: đợt 3 gồm hoá đơn, lịch thanh toán và kiểm tra chuyến đi.</p></li>
</ul>
```

## PR-11 — Visual map planner (last comment 01/10: photos)

```html
<p><span data-type="mention" data-user-id="70121:5793bdd5-44b1-4623-97d4-43c35d440869">@thule</span> Cập nhật trip planner ngày 15/10/2026:</p>
<ul>
<li><p>Trip planner đã có địa chỉ riêng: <a href="https://tripplanner.lumiguides.it.com">tripplanner.lumiguides.it.com</a> (địa chỉ cũ vẫn dùng được).</p></li>
<li><p>Trang tour và trang điểm đến (892 tour, 14 nước) đã chạy: tour chưa có ảnh riêng thì dùng ảnh của điểm đến, chữ đủ độ tương phản để dễ đọc, danh sách tour lọc được theo tháng.</p></li>
<li><p>Bản đồ chịu được nhiều lượt xem cùng lúc (trước đây lúc đông thỉnh thoảng báo lỗi).</p></li>
<li><p>Việc ghép địa điểm trong lịch trình đã chuyển sang hệ thống nội dung: Laos 46/46 tour đã có lộ trình đầy đủ. Trip planner sẽ chuyển sang dùng nguồn mới sau khi tối ưu tốc độ.</p></li>
<li><p>Còn thiếu: phần lớn tour vẫn chưa có ảnh riêng (cần thêm ảnh trong các thư mục Drive như đã hướng dẫn).</p></li>
</ul>
```

## PR-14 — Đăng nhập không cần mật khẩu (last comment 01/10: pricing)

```html
<p><span data-type="mention" data-user-id="70121:5793bdd5-44b1-4623-97d4-43c35d440869">@thule</span> Cập nhật đăng nhập không mật khẩu ngày 15/10/2026:</p>
<ul>
<li><p>Đã chọn AWS Cognito, nhân viên đăng nhập bằng mã gửi qua email công ty (không dùng Google vì mail công ty không nằm trên Google Workspace).</p></li>
<li><p>Đã chuẩn bị xong phần nền: tên miền lumiguides.it.com chuyển sang quản lý trên AWS; dịch vụ gửi email đã xác thực tên miền; chứng chỉ cho trang đăng nhập auth.lumiguides.it.com và staff-auth.lumiguides.it.com đã cấp.</p></li>
<li><p>Đã gửi AWS yêu cầu mở gửi email chính thức (AWS duyệt trong khoảng 1 ngày).</p></li>
<li><p>Bước tiếp: bật đăng nhập bằng mã email cho nhân viên trước, sau đó tới tenant.</p></li>
</ul>
```

## PR-7 — AA social media automation pipeline (comment 10471, corrected 15/10 with 4 inline screenshots)

First version overstated it ("posts really removed on WordPress/Facebook"): only WordPress was run live, via API,
with no screenshots. Redone through the portal UI (screenshots in `aa815/`), then the comment was edited to:

- WordPress: full round trip tested in the portal (connect, publish, post on the site, unpublish, link gone).
- Facebook Page: connect + token check exist; publish/unpublish shipped but not tested on a real Page yet.
- AI policy line, 20 posts/day cap, no AI-written reviews; CTA review warning + admin notice.
- Next: Facebook round trip once a test Page exists; tenant AI terms before 12/11.

## PR-7 — follow-up: Facebook round trip (POSTED 15/10, comment 10472, 4 inline screenshots)

Attach inline: `aa815/facebook/03-portal-published-list-facebook.jpg`, `04b-facebook-post-on-page-admin-view.png`,
`06-portal-unpublished-facebook.jpg`, `08-facebook-page-post-gone-admin-view.png`.

```html
<p><span data-type="mention" data-user-id="70121:5793bdd5-44b1-4623-97d4-43c35d440869">@thule</span> Cập nhật thêm phần Facebook ngày 15/10/2026:</p>
<ul>
<li><p><strong>Facebook Page — đã thử trọn vòng</strong> trên một fanpage thật, thao tác trong portal như tenant: kết nối page → bấm Đăng, bài hiện trên page → bấm Gỡ, bài bị xoá khỏi page. Ảnh từng bước đính kèm bên dưới.</p></li>
<li><p>Lưu ý: app Facebook dùng để thử đang ở chế độ thử nghiệm nên chỉ admin page thấy bài. Để bài hiện công khai cho người theo dõi, app cần chuyển sang chế độ công khai; em sẽ thử chế độ này và viết hướng dẫn kết nối Facebook cho tenant.</p></li>
<li><p>Như vậy cả WordPress và Facebook đều đã thử đăng và gỡ thật.</p></li>
</ul>
<p>Ảnh theo thứ tự: (1) bài đã đăng trong portal, (2) bài trên fanpage, (3) portal sau khi gỡ, (4) fanpage sau khi gỡ.</p>
```

## PR-18 — Quản lý tenant (POSTED 15/10, comment 10473, 1 inline screenshot)

Missed by the first session-end sweep (no S237 work was mapped to it). Posted: admin can set a per-tenant daily
publish limit (Tenant 360 → Settings; default 20/day). Verified live on terra-family: saved 25 → reload 25 → cleared →
20/day (default). Screenshot `ui-verify/cis-admin/tenant360-settings-daily-publish-limit-saved-25.jpg`. Asks chị Thư
to review so the issue can move to Done.
