# S238 — Jira update drafts (NOT posted; Nghiệp approves each before posting)

Site `adventure-asia.atlassian.net`, cloudId `78f9a2ea-f228-4ff6-b37d-7079434d2cef`. Post with `contentFormat: html`;
the mention is `<span data-type="mention" data-user-id="70121:5793bdd5-44b1-4623-97d4-43c35d440869">@thule</span>`.
Tone (Nghiệp, S238): describe the feature that was built; no "như đã hứa", no trailing "ạ". Every claim below was
checked live on Dev in S238 (screenshots in this folder). Status: draft.

---

## PR-7 — Đăng bài lên kênh của tenant (Facebook / WordPress)

Attach: `aa831/connect-card-1440.jpg`, `aa831/guide-390.jpg`.

```html
<p><span data-type="mention" data-user-id="70121:5793bdd5-44b1-4623-97d4-43c35d440869">@thule</span> Cập nhật đăng bài cho tenant ngày 15/10/2026:</p>
<ul>
<li><p>Đã có hướng dẫn kết nối Facebook Page ngay trong portal: ở trang Publish, thẻ "Connect Facebook Page" có link "Step-by-step guide". Hướng dẫn gồm 7 bước: tạo hoặc chọn app Meta, thêm link chính sách riêng tư và chuyển app sang Live, lấy token đủ 3 quyền, đổi sang token dài hạn, lấy Page Access Token, tìm Page ID, rồi bấm Test &amp; Connect.</p></li>
<li><p>Có mục các lỗi hay gặp: token sai hoặc hết hạn, thiếu quyền, bài đăng chỉ chủ app thấy khi app còn ở chế độ Development.</p></li>
<li><p>Chữ hướng dẫn ngay trên thẻ kết nối đã sửa: ghi đủ 3 quyền và nhắc app phải ở chế độ Live.</p></li>
<li><p>Mục Social Content giờ gợi ý chủ đề cho Facebook, Instagram và TikTok (trước đây chỉ gợi ý LinkedIn). Tenant chỉ thấy gợi ý cho các kênh tenant bật.</p></li>
<li><p>Danh sách "Ready to Publish" không còn lặp bài: mỗi chủ đề chỉ hiện bản mới nhất (tenant thử nghiệm Atlas &amp; Hearth từ 48 thẻ còn 3).</p></li>
</ul>
```

## PR-17 — Tenant viết đúng giọng thương hiệu

Attach: `pr17/S238-tenant-voice-samples-Trail-Pulse-Atlas-Hearth.docx` (Nghiệp: upload to the GDrive AdventureAsia
folder and paste the link, or attach directly).

```html
<p><span data-type="mention" data-user-id="70121:5793bdd5-44b1-4623-97d4-43c35d440869">@thule</span> Gửi chị bản đọc thử giọng văn của 2 thương hiệu thử nghiệm, ngày 15/10/2026:</p>
<ul>
<li><p>File đính kèm gồm: tour Mongolia 15 ngày viết lại cho Trail Pulse (năng động) và Atlas &amp; Hearth (văn hoá, chiêm nghiệm), cùng một tour gốc để chị so sánh; 2 bài LinkedIn và 1 bài blog.</p></li>
<li><p>Tất cả đều do hệ thống viết qua luồng tenant thật, em không sửa tay.</p></li>
<li><p>Đã bỏ hẳn dấu gạch dài (—) trong bài viết và trong tour viết lại: hệ thống tự thay bằng dấu phẩy, dấu hai chấm hoặc tách câu. Các bài mới viết hôm nay không còn dấu này.</p></li>
<li><p>Chị đọc thấy câu nào chưa đúng giọng thì đánh dấu giúp em, em dùng để chỉnh tiếp.</p></li>
</ul>
```

## PR-12 — Booking system

Attach: inbox screenshot of `[Dev] New inquiry TC-000005` (Nghiệp's screenshot from 15/10).

```html
<p><span data-type="mention" data-user-id="70121:5793bdd5-44b1-4623-97d4-43c35d440869">@thule</span> Cập nhật Booking ngày 15/10/2026:</p>
<ul>
<li><p>Khi khách gửi chuyến đi từ TripPlanner, nhân viên nhận email báo ngay: tên khách, email, nước, số ngày, các tour và ngày tương ứng, kèm link mở hồ sơ chuyến đi trong Booking. Nếu thông tin khách trùng với khách đã có, email ghi rõ để nhân viên kiểm trước khi gộp.</p></li>
<li><p>Email gửi từ địa chỉ no-reply@lumiguides.it.com; đang gửi về hộp thư anh Nghiệp trên môi trường thử nghiệm.</p></li>
<li><p>Mỗi chặng trong hồ sơ chuyến đi giờ gắn với mã tour cố định của hệ thống nội dung, nên khi tour được cập nhật nội dung, hồ sơ vẫn trỏ đúng tour.</p></li>
</ul>
```

## PR-11 — Visual map planner

```html
<p><span data-type="mention" data-user-id="70121:5793bdd5-44b1-4623-97d4-43c35d440869">@thule</span> Cập nhật trip planner ngày 15/10/2026:</p>
<ul>
<li><p>Trang điểm đến và danh sách tour tải nhanh hơn nhiều khi có nhiều người vào cùng lúc: phần đọc địa điểm của một tour từ khoảng 0,9 giây xuống khoảng 0,01 giây. Hết lỗi trang không tải được khi nhiều trang mở cùng lúc.</p></li>
<li><p>Trang chủ không còn tải trước toàn bộ các trang điểm đến; trang chỉ tải khi khách bấm vào.</p></li>
</ul>
```

---

Not drafted (nothing shipped to report yet): PR-14 (staff email-code login: SES is ready, Cognito not built yet),
PR-18, KAN-20.
