# Bản nháp Jira — gói sẵn sàng pháp lý (S246, 21/10/2026)

Tác nhân: Claude Code. **Chưa đăng.** Nghiệp duyệt nguyên văn trước khi đăng (skill `aa-jira-update`).

- **Nơi đăng:** comment trên epic **PR-27** (Platform). Trong project PR chưa có story pháp lý (JQL ngày 21/10/2026;
  gần nhất là PR-18 và PR-23). Agent không tạo issue Jira; nếu Nghiệp muốn, Nghiệp tạo một story dưới PR-27 rồi đăng
  comment này vào story đó.
- **Định dạng:** `contentFormat: html`, mention bằng thẻ span bên dưới (markdown `@thule` không tạo mention thật).
- **Link GDrive:** agent điều phối thay dòng chữ "LINK GDRIVE" bằng link thật sau khi tải lên và Nghiệp mở quyền chia sẻ.
- Không mã issue nội bộ, không "ạ"; chỉ nêu những gì đã kiểm trên môi trường chạy thật.

## Nội dung comment (HTML)

```html
<p><span data-type="mention" data-user-id="70121:5793bdd5-44b1-4623-97d4-43c35d440869">@thule</span> Chị Thư, em gửi chị gói tài liệu pháp lý cho Trip Planner và Partner Portal.</p>

<p><strong>Đã làm xong</strong></p>
<ul>
  <li>Trip Planner và Partner Portal mỗi bên đã có trang chính sách quyền riêng tư và trang điều khoản bản nháp. Bốn trang đang chạy, có nhãn "Draft — pending legal review", không cho công cụ tìm kiếm lập chỉ mục, và được dẫn link ở chân trang, ở trang đăng nhập portal, và ngay cạnh ô đồng ý của form liên hệ Trip Planner:
    <ul>
      <li>aa-tripplanner.vercel.app/privacy và /terms</li>
      <li>portal.lumiguides.it.com/privacy và /terms</li>
    </ul>
  </li>
  <li>Ghi nhận sự đồng ý đã được kiểm trên hệ thống thật ngày 20/10/2026: em gửi một yêu cầu thử qua form Trip Planner, có tích ô đồng ý. Hệ thống lưu "đồng ý", ngày giờ và nguồn ở cả Trip Planner lẫn hệ thống đặt tour, hai bên khớp nhau; trên toàn bộ dữ liệu có 0 trường hợp lệch.</li>
</ul>

<p><strong>Trong gói tài liệu</strong> (song ngữ Anh–Việt): LINK GDRIVE</p>
<ul>
  <li>Bản tóm tắt 12 chủ đề, mỗi chủ đề có hiện trạng, các phương án và một đề xuất.</li>
  <li>Sổ đăng ký dữ liệu cá nhân được xử lý và danh sách nhà cung cấp dịch vụ nhận dữ liệu.</li>
  <li>Bản nháp thỏa thuận xử lý dữ liệu cho đối tác, kèm phụ lục biện pháp bảo mật (ghi rõ biện pháp nào đang chạy, biện pháp nào mới dự kiến).</li>
  <li>Quy trình nhận và trả lời yêu cầu xem hoặc xoá dữ liệu (chưa chạy thử; tìm bản ghi bằng mã băm của e-mail và xoá theo mã số bản ghi, nên địa chỉ e-mail không bị ghi vào mã nguồn hay nhật ký), và sổ ghi các lần xoá theo thời hạn lưu trữ.</li>
</ul>
<p>Hệ thống chưa có dữ liệu thật của khách du lịch hay khách hàng: khi kiểm ngày 17/10/2026, mọi bản ghi khách đều là bản ghi thử hoặc nội bộ. Tài khoản nhân viên, người nhận e-mail cảnh báo và danh mục tour là dữ liệu thật.</p>

<p><strong>Các điểm cần chị quyết định</strong> (đề xuất ở từng mục trong gói):</p>
<ol>
  <li>Pháp nhân chịu trách nhiệm dữ liệu và địa chỉ đăng ký ghi trên các trang.</li>
  <li>Các điểm kinh doanh trên trang: tuổi tối thiểu, thời hạn trả lời yêu cầu, điều kiện đặt tour, phí.</li>
  <li>Danh sách nhà cung cấp dịch vụ: liệt kê đủ, kể cả đại lý bán lại AWS, hay chỉ các bên trực tiếp xử lý dữ liệu.</li>
  <li>Chuyển dữ liệu ra nước ngoài: máy chủ đặt tại Mỹ; một phần xử lý AI có thể chạy ngoài Mỹ.</li>
  <li>Cam kết dịch vụ cho đối tác, địa chỉ hỗ trợ <code>support@</code>, trang trạng thái.</li>
  <li>Thời điểm chuyển Vercel lên gói Pro.</li>
  <li>Điều khoản sử dụng AI cho đối tác: cần chị trả lời trước ngày 11/11/2026, vì chính sách của Anthropic có hiệu lực từ 12/11/2026.</li>
</ol>
<p>Có cần mời luật sư xem gói này hay không, và cho chủ đề nào, là chị quyết định.</p>
```
