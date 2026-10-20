# CRM cho đại lý: những việc cần chị Thư cho ý kiến

Chị Thư ơi,

Bên em đang làm phần CRM cho đại lý (nằm trong tenant portal), đúng theo spec chị đưa. Phần kỹ thuật bên em tự lo.
Còn những việc dưới đây là chuyện kinh doanh, pháp lý, tiền hoặc chọn dịch vụ bên ngoài, nên em xin ý kiến của chị.

Trước khi vào câu hỏi, có hai điều để chị yên tâm:
- **Bây giờ chưa có gì gấp.** Anh Nghiệp đã chốt: làm xong đủ 23 phần của spec rồi mới cho đại lý thật dùng. Trong
  lúc làm, bên em thử bằng **đại lý giả, dữ liệu giả**, nên chưa phải trả tiền cho dịch vụ nào bên dưới.
- Mỗi câu đều có **đề xuất** của bên em. Chị chỉ cần đánh dấu "đồng ý", hoặc ghi ý của chị.

Giá ghi bằng USD, em xem trên trang của từng hãng ngày 20/10/2026.

---

## 1. Giá cho đại lý

**1.1 (H2) Đại lý trả gì để dùng CRM?**
- Spec ghi "miễn phí cho đối tác". Anh Nghiệp đề xuất thêm: CRM đi theo **gói của tenant portal**, tức đại lý ở gói
  portal nào thì có phần CRM tương ứng.
- Em đề xuất:
  - các phần chính miễn phí ở mọi gói;
  - gói cao hơn có thêm AI soạn nháp, báo cáo đầy đủ, nhiều người dùng hơn;
  - đại lý tự trả các phí của bên thứ ba qua tài khoản của họ: tin WhatsApp, SMS, phí thẻ.
- Chi phí AA gánh (ước tính): khoảng $8–9 một đại lý mỗi tháng khi có 10 đại lý, chưa tính tiền ký điện tử (xem 3.1).
  Con số giảm dần khi có nhiều đại lý hơn.
- Chị cho em biết: chia tính năng theo gói thế nào, hoặc cứ để miễn phí hết như spec?

**1.2 (H9) Giá net cho đại lý.**
- Em đề xuất dùng bảng giá net B2B đang có (biên 15%), và đại lý tự đặt giá bán cho khách của họ.
- Anh Nghiệp để chị quyết.

**1.3 AA thu tiền đại lý thế nào khi đại lý bán tour của AA?**
- Theo quyết định cũ, AA xuất hoá đơn cho đại lý.
- Chị cho em biết các điều sau:
  - đại lý trả trước hay được nợ;
  - cọc bao nhiêu %;
  - xuất hoá đơn bằng tiền gì;
  - phí thẻ 3% có áp cho chuyển khoản không.

**1.4 Có cấm đại lý báo giá thấp hơn giá "từ …" công khai của AA không?**
- Em đề xuất chỉ ghi trong hợp đồng, CRM chỉ cảnh báo chứ không chặn.

**1.5 Ai nhập giá net của nhà cung cấp và bảng giá tour vào hệ thống Booking, và khi nào?**
- Báo giá tự động cho khách cần số liệu này.
- Trong lúc chờ, bên em dùng giá giả để thử.

---

## 2. Pháp lý và hợp đồng

**2.1 (H5) Ký hợp đồng với đại lý bằng pháp nhân nào của AA, và có cần luật sư ngay không?**
- Em đề xuất:
  - ký bằng pháp nhân AA đang dùng cho hợp đồng đối tác (chị cho em tên);
  - dùng mẫu thoả thuận dữ liệu (DPA) em đã soạn;
  - **chưa cần luật sư khi chưa có đại lý thật**.
- Em soạn sẵn bản tóm tắt cho luật sư, và chỉ gửi khi có một trong ba điều:
  - đại lý ở Việt Nam hoặc châu Âu muốn dùng dữ liệu thật;
  - có đại lý thứ 6;
  - 60 ngày sau khi có khách thật đầu tiên.

**2.2 Câu hứa về quyền riêng tư cần sửa thêm một chút.**
- Anh Nghiệp đã tạm đồng ý thay chị câu "nhân viên AA không mở được hồ sơ khách" (H3). Về kỹ thuật thì AA sở hữu tài khoản máy chủ, nên trong
  trường hợp khẩn cấp vẫn mở được.
- Em đề xuất hứa đúng như sau: "Nhân viên AA không mở được hồ sơ khách trong công việc bình thường. Chỉ trong trường
  hợp khẩn cấp mới mở được, mỗi lần một đại lý, phải đăng nhập hai bước, và việc đó tự động hiện trong nhật ký của
  chính đại lý."

**2.3 AA hỗ trợ có được xem vào CRM của đại lý không?**
- Em đề xuất: chỉ khi chủ đại lý tự bật quyền cho AA trong phần cài đặt, có thời hạn (ví dụ 24 giờ). Mọi lần xem đều
  được ghi lại, và chủ đại lý tắt được bất cứ lúc nào.

**2.4 Khi khách hoặc đại lý yêu cầu xoá dữ liệu, mình hứa gì?**
- Em đề xuất: "Xoá ngay trong ứng dụng. Không đọc lại được ở bất kỳ đâu, kể cả bản sao lưu, trong vòng 30 ngày."

**2.5 Nhật ký "ai đã xem gì" giữ bao lâu?**
- Em đề xuất: đại lý xem được trong 12 tháng, sau đó lưu khoá (không sửa được) thêm 6 năm, trừ khi luật sư khuyên
  khác.

**2.6 Khi AA ops xem thông tin khách của chuyến đã chốt, có báo cho đại lý không?**
- Em đề xuất có: đại lý thấy dòng "AA ops đã xem thông tin chuyến X ngày Y".

**2.7 AA ops được gửi thông tin khách nào cho khách sạn, xe?**
- Gửi đi là có bản sao nằm ngoài hệ thống, không tự xoá sau 90 ngày được.
- Em đề xuất:
  - chỉ gửi họ tên, số người, yêu cầu ăn uống/đi lại;
  - không gửi số hộ chiếu, trừ khi nhà cung cấp bắt buộc;
  - mỗi lần xuất danh sách đều được ghi lại.

**2.8 Khách của đại lý sẽ thấy địa chỉ web và email gửi đi tên gì?**
- Hiện bên em dùng tên miền thử nghiệm. Có ba lựa chọn:
  - một tên miền chung mang tên AA;
  - một tên miền trung tính cho sản phẩm;
  - mỗi đại lý dùng tên miền riêng của họ (đại lý tự cài đặt).
- Mua tên miền mới thường vài chục USD mỗi năm (ước tính).
- Em đề xuất: một tên miền trung tính, và cho đại lý nào muốn thì dùng tên miền riêng.

**2.9 Đăng nhập mạnh hơn cho nhân viên đại lý.**
- Nhân viên đại lý xem được số hộ chiếu của khách, nên em đề xuất chủ đại lý và nhân viên bán hàng đăng nhập thêm một
  bước: passkey trên điện thoại, hoặc app xác thực. Lần đầu mất thêm khoảng 1 phút.
- Chị thấy đại lý có chịu không?

**2.10 Dịch vụ AI chạy ở tài khoản máy chủ thứ hai của AA.**
- Tài khoản này mua qua một đơn vị khác (eCloudvalley). Em sẽ ghi nó vào danh sách "bên xử lý dữ liệu" trong hợp đồng
  với đại lý.
- Chị đồng ý không? Nếu chị không muốn, phần AI sẽ tắt cho tới khi có cách khác.

---

## 3. App và dịch vụ bên ngoài có phí

Tất cả các mục dưới đây **chưa cần trả tiền**: trên môi trường thử, bên em dùng bản miễn phí hoặc bản test. Chỉ cần
quyết trước khi có đại lý thật.

**3.1 Ký điện tử (khách ký điều khoản và waiver trekking)**
- **Là gì:** khách bấm ký điều khoản và waiver ngay trên trang của đại lý, hệ thống lưu bản PDF đã ký kèm nhật ký
  ký.
- **Spec đòi:** ký điện tử, lưu PDF và nhật ký ký, và **hãng bảo hiểm chấp nhận**. Spec không chỉ định hãng nào.
- **Lựa chọn:**

  | Lựa chọn | Phí cho AA | Ghi chú |
  |---|---|---|
  | Documenso Teams | $40/tháng, trả $480 một năm | Trang ký có thể hiện chữ "Documenso"; tối đa 5 người dùng |
  | Documenso Platform | $250/tháng, trả $3.000 một năm | Mang thương hiệu riêng, không giới hạn |
  | BoldSign API | từ $30/tháng, gồm 40 lượt ký, thêm $0,75 mỗi lượt | Rẻ khi ít khách; có thương hiệu riêng |
  | Dropbox Sign API | từ $75/tháng ($900/năm) | Hãng lớn, đắt hơn |
  | Tự cài Documenso trên máy chủ của AA | ≈ $5–17/tháng + chứng thư số (giá chưa rõ) | Dữ liệu không ra ngoài; bên em tự vận hành |
  | AA tự làm chữ ký điện tử đơn giản | ≈ $0–1/tháng | Khách nhận mã qua email, gõ tên, bấm "Tôi đồng ý"; hệ thống niêm phong PDF |

- **Đề xuất:**
  1. Hỏi hãng bảo hiểm trước, vì họ chấp nhận cách nào thì mình chọn cách đó.
  2. Nếu họ chấp nhận chữ ký đơn giản thì **AA tự làm** (rẻ nhất, dữ liệu không ra ngoài).
  3. Nếu họ muốn hãng có tên tuổi thì chọn **BoldSign**, hoặc **Documenso Teams** cho giai đoạn đầu.

**3.2 WhatsApp (và Messenger, Instagram)**
- **Là gì:** đại lý nhắn tin với khách ngay trong CRM, bằng tài khoản WhatsApp Business của chính đại lý.
- **Phí:** AA $0. Meta tính phí tin nhắn thẳng vào thẻ của đại lý.
- **Cần làm:** AA đăng ký làm "Tech Provider" với Meta. Việc này cần xác minh doanh nghiệp và Meta duyệt app, mất 2–4
  tuần trở lên, và cần đứng tên một pháp nhân AA.
- **Lựa chọn khác:** spec ghi Twilio hoặc 360dialog. Hai hãng này thu thêm phí trung gian.
- **Đề xuất:**
  - đi thẳng với Meta (rẻ nhất);
  - chị cho em biết pháp nhân nào đăng ký;
  - bắt đầu thủ tục khi chị chọn đại lý thật đầu tiên, hoặc sớm hơn nếu chị muốn kịp giờ.

**3.3 SMS (Twilio)**
- **Là gì:** gửi tin SMS cho khách.
- **Phí:** AA $0. Mỗi đại lý dùng tài khoản Twilio của chính họ và tự trả.
- **Đề xuất:** đồng ý cách này.

**3.4 Thanh toán thẻ (Stripe)**
- **Là gì:** khách trả cọc và trả nốt bằng link thanh toán; tiền vào thẳng tài khoản Stripe của đại lý.
- **Phí:** AA $0. Stripe tính phí thẻ vào đại lý.
- **Lưu ý:** Stripe **không hoạt động ở Việt Nam**.
- **Cần làm:** để tiền vào thẳng tài khoản của đại lý, AA cần một tài khoản Stripe làm "nền tảng" (Stripe Connect),
  đứng tên một pháp nhân AA. Trên môi trường thử chỉ cần tài khoản ở chế độ test, miễn phí. Chị cho em biết pháp nhân
  nào đứng tên tài khoản thật.
- **Đề xuất:** dùng Stripe cho đại lý ở nước có Stripe (ví dụ Úc).

**3.5 Cổng thanh toán cho đại lý Việt Nam**
- **Là gì:** cổng thanh toán nội địa thay cho Stripe.
- **Phí:** chưa có báo giá.
- **Đề xuất:**
  - trong lúc chờ, đại lý ghi tay khoản đã thu;
  - chị chọn giúp em vài cổng để xin báo giá;
  - mục này chưa gấp, vì đại lý Việt Nam chưa dùng dữ liệu thật.

**3.6 Gửi email bằng Gmail của đại lý (Google)**
- **Là gì:** email trả lời khách gửi từ chính Gmail của đại lý, và nằm trong hộp "Đã gửi" của họ.
- **Phí:** $0. Bên em cố ý **chỉ xin quyền "gửi thư"**, nên tránh được đợt kiểm định bảo mật bắt buộc mỗi năm của
  Google (gọi là CASA). Theo tìm hiểu trước đây, CASA tốn khoảng $675–5.400 mỗi năm, có nơi ghi cao hơn nhiều; Google
  không công bố bảng giá.
- **Cần làm:** Google xác minh app (miễn phí). Việc này cần trang chủ và chính sách quyền riêng tư trên tên miền của
  AA.
- **Đề xuất:** chị cho em biết pháp nhân và tên miền đứng tên.

**3.7 Gửi email bằng Outlook (Microsoft)**
- **Là gì:** như 3.6, cho đại lý dùng Outlook.
- **Phí:** $0. Cần AA có tài khoản tổ chức Microsoft 365 và tham gia chương trình đối tác miễn phí của Microsoft.
- **Đề xuất:** làm sau Gmail, khi có đại lý dùng Outlook.

**3.8 Tường lửa web cho trang khách**
- **Là gì:** chặn tấn công và spam trên form và trang của khách.
- **Phí:** ≈ $7–8/tháng, chỉ bật khi có đại lý thật.
- **Đề xuất:** bật lúc có đại lý thật. AA chịu khoản này.

**3.9 Luật sư**
- **Là gì:** xem luật dữ liệu Việt Nam, châu Âu, Úc, hợp đồng đối tác và waiver.
- **Phí:** chưa có báo giá.
- **Đề xuất:** giữ như anh Nghiệp đã chốt: chưa gửi bây giờ, gửi khi chạm một trong các mốc ở 2.1.

---

## 4. Bảo hiểm và waiver

**4.1 (H6) Nhờ hãng bảo hiểm nào duyệt waiver trekking?**
- Em đề xuất nhờ hãng bảo hiểm AA đang dùng. Chị cho em tên người liên hệ khi tiện.
- Em xin hỏi họ thêm một câu: **họ chấp nhận cách ký điện tử nào** (mục 3.1). Câu trả lời này quyết định mình chọn
  dịch vụ nào.

**4.2 (H10, anh Nghiệp đã tạm đồng ý thay chị) Mẫu điều khoản và waiver.**
- AA soạn một mẫu song ngữ Anh–Việt dựa trên điều khoản hiện tại. Đội của chị xem lại, và hãng bảo hiểm duyệt.
- Em chỉ báo để chị nắm, không cần trả lời.

---

## 5. Đại lý thử nghiệm

**5.1 (H4) Dùng đại lý giả trước — em báo để chị biết.**
- Theo ý anh Nghiệp, bên em tạo vài **đại lý giả, khách giả** để thử toàn bộ quy trình trên môi trường thử. Chị không
  cần làm gì lúc này.
- Khi đủ 23 phần (dự kiến khoảng giữa tháng 12/2026 tới giữa tháng 1/2027, còn tuỳ tiến độ), em xin chị chọn **3–5 đại lý thân quen**. Em đề
  xuất chọn ở Úc hoặc nước khác ngoài châu Âu và Việt Nam, và mỗi đại lý em xin 30 phút phỏng vấn trước khi mở.

**5.2 (H1, đã chốt) Chờ xong cả 23 phần mới cho đại lý thật dùng.**
- Em ghi lại để mọi người cùng hiểu.
- Ngày 30/11 trước đây chỉ là dự kiến, không còn là hạn chót.

**5.3 Khi nào bắt đầu các thủ tục với Meta, Google, Microsoft?**
- Các thủ tục này mất vài tuần mỗi cái.
- Em đề xuất bắt đầu khi chị chọn xong đại lý thật đầu tiên. Nếu chị muốn mở đúng ngày cho đại lý thì bắt đầu sớm
  hơn khoảng một tháng.

**5.4 (H8, anh Nghiệp đã tạm đồng ý thay chị) Ai ở đội ops phụ trách nhập lịch khởi hành và xác nhận các tour "theo yêu cầu" trong 1 ngày làm
việc?**
- Chị cho em tên người khi tiện.

---

## 6. Các mục anh Nghiệp đã tạm trả lời thay chị

Chị xem lại cho chắc. Nếu đồng ý thì không cần làm gì; muốn đổi mục nào thì chị ghi lại giúp em.
- **H3:** câu hứa về quyền riêng tư (đã sửa thêm ở 2.2).
- **H7:** bản đầu chưa làm Zalo.
- **H8:** tour có lịch cố định thì tự xác nhận; tour khác là "theo yêu cầu", AA ops xác nhận trong 1 ngày làm việc
  (5.4).
- **H10:** AA soạn mẫu điều khoản và waiver song ngữ (4.2).
- **H11:** AA chỉ xem số liệu tổng hợp của nhóm có ít nhất 10 khách, đến từ ít nhất 3 đại lý, và chỉ của đại lý tự
  chọn tham gia.
- **H12:** anh Nghiệp tạm chọn Documenso Teams cho giai đoạn đầu. Sau đó anh muốn chị quyết lại cùng các lựa chọn khác
  ở 3.1, nên mục 3.1 mới là câu cần chị trả lời.

Em cảm ơn chị. Chị trả lời mục nào trước cũng được. Những mục gắn "đã chốt" hoặc "đã tạm đồng ý" chỉ để chị nắm.
