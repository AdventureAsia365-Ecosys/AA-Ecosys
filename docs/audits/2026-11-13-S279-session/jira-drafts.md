# S279 — nháp Jira (chờ tech lead duyệt)

Quy tắc: chỉ báo tính năng đã ship và kiểm live; không câu hỏi cho chị Thư; không mã issue nội bộ; mention @thule bằng
mention node khi đăng. Không đăng PR-27 (hạ tầng): quyết định kỹ thuật thuộc tech lead. Link trang video là artifact
riêng tư: tech lead mở quyền chia sẻ cho chị Thư trước khi đăng.

## PR-22 — CIS

@thule Cập nhật CIS (13–14/11):

1. Trang Cài đặt nền tảng (Platform › Settings): các ngưỡng, giới hạn và trần chi phí của CIS, Booking, CRM và
   TripPlanner chỉnh được ngay trên trang, không cần sửa code. Mỗi thông số có giải thích tiếng Anh và tiếng Việt (là
   gì, tăng hay giảm thì sao, khi nào nên chỉnh, ví dụ), có người duyệt, lịch sử thay đổi, nhận dấu phẩy thập phân và
   hiện tên người đã đổi.
2. Khi một đại lý ngừng hợp tác: hệ thống xoá hoặc ẩn danh dữ liệu cá nhân của đại lý đó ở mọi app theo lịch đã chốt,
   luôn chạy thử trước và cần người duyệt trước khi xoá thật. Đã diễn tập đầy đủ trên đại lý thử nghiệm (chạy thử, báo
   cáo từng app, khôi phục lại); lần xoá thật đầu tiên trên đại lý thử nghiệm sẽ chạy trong buổi tới.
3. Sao lưu và khôi phục riêng từng đại lý cho nội dung CIS và TripPlanner: đã khôi phục thử thành công trên đại lý thử nghiệm.

## PR-25 — Booking

@thule Cập nhật Booking (13–14/11):

1. Bảng giá theo phiên bản và lịch mùa: giá nhập tay theo mùa và ngày lễ nằm trong từng phiên bản bảng giá; phiên bản
   mới cần người thứ hai duyệt mới có hiệu lực; báo giá và bảng giá cho đại lý đọc đúng phiên bản đang áp dụng. Trên Dev
   đang có 7 phiên bản (2 đang áp dụng, 5 đã rút).
2. Trang Chính sách giá giải thích từng thông số bằng tiếng Anh và tiếng Việt, nhận dấu phẩy thập phân.
3. Nhập giá hàng loạt bằng Excel cho nhiều tour (chạy thử trước khi ghi, hai người duyệt): đã có trong hệ thống, sẽ thử
   trọn vòng với giá giả lập trong buổi tới.

## PR-26 — CRM cho đại lý

@thule Cập nhật CRM đại lý (13–14/11):

1. Dòng tour AA đã được AA xác nhận nay hiện cho khách trên cổng của khách theo mặc định; đại lý bật hoặc tắt từng dòng
   bằng nút "Hiện cho khách".
2. Khi đại lý thêm tour AA vào đề xuất, lịch trình đề xuất tự chép các ngày và điểm đến của tour (đại lý vẫn sửa được).
   Đã kiểm trên cổng của khách thử nghiệm: lịch trình 7 ngày có tiêu đề và địa điểm từng ngày, mục "Đã đặt" có tour,
   có voucher.
3. Đã có trong hệ thống, chưa thử trọn vòng: khi AA ngừng phục vụ một tour, CRM gắn cờ các chuyến và đề xuất của đại lý
   đang dùng tour đó để đại lý xử lý.

## PR-20 — Báo cáo định kỳ (diễn tập pilot)

@thule Diễn tập pilot ngày 13/11 trên một đại lý thử nghiệm, đi trọn hành trình qua 5 app: tạo đại lý, thương hiệu và
bài viết trên Content studio (đăng thử WordPress và Facebook rồi gỡ), khách lập kế hoạch trên TripPlanner, yêu cầu vào
CRM, báo giá, khách chấp nhận và đặt cọc, AA xác nhận booking, đặt dịch vụ nhà cung cấp, cổng của khách (hộ chiếu, lịch
trình, voucher), kế toán hai người duyệt.

- 34 video có tiếng Anh và tiếng Việt: 32 đạt, 2 không đạt (1 do kịch bản quay, đã sửa; 1 là lỗi cổng khách đã sửa
  và quay lại đạt).
- Chi phí AI cả buổi: 0,49 USD.
- Trang tóm tắt từng video (quay gì, kết quả, link): https://claude.ai/artifact/9KCRRJ1cuGULqBHZeVeAmC.
- Còn lại cho buổi sau: Đặt tour online (cần bật cho đại lý), nhập giá, và các bước ngân sách của pilot thật.

## Kết quả đăng

Tech lead duyệt "Đăng" (14/11/2026). Đã đăng nguyên văn:

- PR-22: https://adventure-asia.atlassian.net/browse/PR-22?focusedCommentId=10649
- PR-25: https://adventure-asia.atlassian.net/browse/PR-25?focusedCommentId=10650
- PR-26: https://adventure-asia.atlassian.net/browse/PR-26?focusedCommentId=10651
- PR-20: https://adventure-asia.atlassian.net/browse/PR-20?focusedCommentId=10652
