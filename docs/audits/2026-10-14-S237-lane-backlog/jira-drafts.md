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

## PR-7 — AA social media automation pipeline (last comment 14/10: quality r5)

```html
<p><span data-type="mention" data-user-id="70121:5793bdd5-44b1-4623-97d4-43c35d440869">@thule</span> Cập nhật phần đăng bài của tenant ngày 15/10/2026:</p>
<ul>
<li><p>Tenant kết nối được Facebook Page trong portal, bên cạnh WordPress.</p></li>
<li><p>Tenant tự gỡ được bài đã đăng: bài bị gỡ thật trên WordPress/Facebook chứ không chỉ đổi trạng thái. Đã thử trọn vòng trên một trang WordPress thử nghiệm: đăng, kiểm bài hiện trên site, gỡ, bài không còn công khai.</p></li>
<li><p>Theo chính sách AI mới (hiệu lực 12/11): portal hiện dòng nhắc "nội dung do AI tạo, tenant chịu trách nhiệm" ở bước duyệt, đăng và xuất bài; mỗi tenant tối đa 20 bài/ngày (admin chỉnh được); AI không viết review, đánh giá hay lời khách hàng.</p></li>
<li><p>Mới thêm: khi tenant nhập câu kêu gọi cuối bài có nhắc review hay số sao, portal nhắc tenant chỉ dùng nếu review là thật, và báo cho admin AA để theo dõi.</p></li>
<li><p>Bước tiếp: hoàn thiện điều khoản sử dụng AI cho tenant trước 12/11.</p></li>
</ul>
```
