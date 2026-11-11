---
title: S277 Jira drafts
lang: vi
---

# S277: nháp Jira (chờ tech lead duyệt rồi mới đăng)

Bốn comment, mỗi comment trên epic của một app. Mỗi comment tag @thule bằng mention node khi đăng. Ảnh đính kèm ghi ở cuối mỗi nháp.

## PR-22 (CIS: nội dung và pipeline)

@thule Cập nhật nội dung tour ngày 11/11 (Dev):

- **Đính chính số "280 tour cần sửa" trong cập nhật 10/11.** Khi chạy thử thật, các tour này hoá ra không có lỗi trên trang. Phần khác biệt chỉ là cách trình bày dòng bữa ăn, nơi ngủ và quãng đường: bản đang bán viết thành câu dễ đọc ("Meals: breakfast, dinner"), còn cách dựng mới chép nguyên mã trong file nguồn ("Meals: B, D"). Bản đang bán dễ đọc hơn, nên các tour giữ nguyên, không sửa theo đợt nữa.
- **Mọi tour đang bán nay đều viết bằng bộ viết mới.** Không còn tour đang bán nào dùng bản viết của bộ cũ.
- **Tour có cưỡi voi:** theo chính sách 08/10, 48 tour có hoạt động cưỡi voi đã được hệ thống tự rút khỏi danh sách bán và chuyển vào hàng chờ duyệt.
- **Bài blog cho đại lý:** hệ thống chỉ lập kế hoạch bài blog cho tour có ít nhất 600 từ dữ kiện đầu vào, để bài đủ dài ngay từ lần viết đầu. Bước viết bổ sung cho bài ngắn đã thử trên 3 bài nhưng không hiệu quả (tour có quá ít dữ kiện để viết thêm), nên không dùng.
- **Ghi chú file nguồn:** tour "Kayak and Hike Wild Thailand" ghi thời lượng 9 ngày, nhưng lịch trình trong file có đủ Day 1 đến Day 10. Hệ thống đã sửa thành 10 ngày; dòng này trong file Excel gốc nên sửa theo để lần nhập sau khớp.

## PR-24 (TripPlanner)

@thule Cập nhật TripPlanner ngày 11/11 (Dev, https://tripplanner.lumiguides.it.com):

- **Trang lên lịch trình mới:**
  - mỗi điểm dừng và mỗi ngày có ảnh, kèm biểu tượng theo loại hoạt động;
  - bản đồ và danh sách sáng cùng nhau khi chọn một điểm;
  - kéo thả để đổi thứ tự ngày và điểm dừng, dùng được trên điện thoại;
  - trang chia sẻ, in và tải lịch (.ics).
- **Trò chuyện để lên lịch trình (Plan with chat):**
  - Khách gõ yêu cầu, ví dụ "4 days in Laos", và nhận một lịch trình chỉ gồm tour và địa điểm của Adventure Asia; bấm "Apply to my trip" để đưa vào lịch trình.
  - Yêu cầu về nước Adventure Asia không bán (ví dụ Peru) được từ chối lịch sự, kèm danh sách các nước Adventure Asia có tour.
  - Đã thử thật trên Dev: đề xuất đúng, áp vào lịch trình đúng thứ tự, tên địa điểm bịa không lọt qua.
  - Chi phí AI có trần 2 USD mỗi tháng cho cả trang và cho từng đại lý. Hôm nay toàn bộ các lượt thử tốn khoảng 0,07 USD.
- **Trang tải nhanh hơn:** điểm hiệu năng của Google Lighthouse trên điện thoại cho trang lên lịch trình tăng từ 45 lên 62; thời gian hiện nội dung chính giảm từ 4,9 giây xuống 2,6 giây.

Ảnh: trang lịch trình với khung chat (máy tính và điện thoại).

## PR-25 (Booking)

@thule Cập nhật Booking ngày 11/11 (Dev, dữ liệu thử):

- **Vận hành booking của đại lý:**
  - nhân viên Adventure Asia nhập booking thay đại lý (khi đại lý gửi qua email);
  - voucher dịch vụ cho đại lý (không có tên khách, không có giá);
  - danh sách đoàn theo ngày khởi hành (số người lớn, trẻ em, em bé, số phòng);
  - huỷ booking thay đại lý, giảm hoặc miễn phí huỷ cần người thứ hai duyệt;
  - huỷ bớt một phần chỗ;
  - giá trẻ em, em bé và phụ thu phòng đơn cho đại lý;
  - điều khoản đặt cọc và thanh toán riêng cho từng tour.
- **Chi phí và lợi nhuận:**
  - chi phí nhà cung cấp quy về USD;
  - chi phí chung của ngày khởi hành chia theo số khách;
  - đơn đặt dịch vụ gửi nhà cung cấp;
  - so chi phí dự kiến với hoá đơn thực tế;
  - lãi theo từng booking, từng ngày khởi hành và từng đại lý.
- **Ngày khởi hành:**
  - số khách tối thiểu, ngày chốt bán, ngày quyết chạy hay huỷ;
  - tạo hàng loạt ngày khởi hành theo lịch tuần hoặc tháng;
  - giữ chỗ riêng cho đại lý, tự trả lại chỗ chưa bán.
- **Bảng ngày khởi hành mới (Operations → Departures):**
  - lịch tháng và bảng mọi ngày khởi hành: tỷ lệ lấp chỗ, chỗ đã bán, chỗ đang giữ cho đại lý, ngày có nguy cơ không đủ khách;
  - mở một ngày khởi hành để xem chỗ theo từng đại lý, kèm phiếu vận hành (điểm hẹn, giờ hẹn, hướng dẫn viên, trưởng đoàn, tài xế; điểm hẹn và giờ hẹn được gửi sang CRM của đại lý);
  - phí thu đại lý khi đoàn không đủ khách tối thiểu hoặc chỗ giữ riêng không dùng hết; người thứ hai duyệt rồi phí mới vào hoá đơn đại lý. Điều khoản về khoản phí này đang ở dạng nháp, chỉ hiện cho đại lý sau khi chị duyệt nội dung;
  - điều chỉnh giá theo từng ngày khởi hành (người thứ hai duyệt) và giảm giá đặt sớm theo số ngày đặt trước.
- Đã kiểm từng màn hình bằng trình duyệt trên Dev, đăng nhập tài khoản nhân viên thử. Dev còn ít dữ liệu thương mại, nên phần ghi dữ liệu (nhập booking, huỷ, voucher) được kiểm bằng bộ kiểm tự động.

Ảnh: Costs & profit, danh sách đoàn, ngăn ngày khởi hành.

## PR-26 (CRM cho đại lý)

@thule Cập nhật CRM cho đại lý ngày 11/11 (Dev, đại lý thử Sen Vàng, dữ liệu thử):

- **Cộng tác viên và đại lý con:**
  - Đại lý thêm cộng tác viên, chọn cách tính hoa hồng (phần trăm, số tiền mỗi khách hoặc giá net) và gắn cộng tác viên vào chuyến.
  - Khi chuyến được đặt, hoa hồng tự ghi nhận và tính vào chi phí của chuyến. Ví dụ chuyến thử: hoa hồng 10% trên 300 USD = 30 USD.
  - Mỗi cộng tác viên có đường link riêng để xem các chuyến mình giới thiệu.
- **Nút "Book now" trên trang tour của đại lý và thanh toán online:**
  - Khách chọn ngày khởi hành và số khách, xem giá, đặt, rồi trả cọc online qua cổng VNPay bằng tài khoản VNPay của chính đại lý.
  - Mặc định tắt; mỗi đại lý tự bật.
  - Đã thử trọn vòng ở chế độ thử của VNPay (không có tiền thật): đặt, giữ chỗ, chấp nhận, trả cọc, hoá đơn chuyển "đã trả", chuyến chuyển "đã đặt".
  - Khi giá bán lẻ của đại lý thấp hơn giá Adventure Asia (ví dụ 1 khách và đại lý chưa đặt mức cộng giá), trang báo khách "giá cho nhóm này được báo riêng" thay vì bán lỗ.
- Chưa thử với tài khoản VNPay thật, vì mỗi đại lý dùng tài khoản riêng của mình.

Ảnh: trang cộng tác viên, ô Book now có giá, ô thanh toán trên trang khách, trang thanh toán thử.

## Kết quả đăng (tech lead duyệt 11/11/2026)

| Epic | Comment | Ảnh |
|---|---|---|
| PR-22 | 10641 | không có |
| PR-24 | 10642 | chờ gắn (VPN chặn api.media.atlassian.com lúc đăng) |
| PR-25 | 10643 | chờ gắn |
| PR-26 | 10644 | chờ gắn |
