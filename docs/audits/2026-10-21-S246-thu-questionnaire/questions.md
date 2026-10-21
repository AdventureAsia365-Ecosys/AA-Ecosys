# CRM cho đại lý: bảng hỏi quyết định kinh doanh, pháp lý và chi phí

Bảng hỏi này gom các quyết định kinh doanh, pháp lý và chi phí cho CRM đại lý (nằm trong tenant portal), bám theo spec `partner-crm-spec.md`. Phần kỹ thuật không nằm ở đây.
Mỗi câu có 2–4 lựa chọn a/b/c(/d); lựa chọn đề xuất có ghi lý do. Chọn một lựa chọn, hoặc ghi ý khác. Câu ghi “cần xác nhận” đã có câu trả lời tạm, chỉ cần xác nhận hoặc sửa.
Không có câu nào gấp: đại lý thật chỉ dùng sau khi đủ 23 module; trên Dev chỉ có đại lý giả, dữ liệu giả, chưa phát sinh chi phí dịch vụ nào bên dưới.

Ghi chú: giá đối thủ kiểm ngày 21/10/2026; giá dịch vụ bên ngoài xem ngày 20/10/2026, tính bằng USD. Mã trong ngoặc vuông (ví dụ [Q1.1, R11]) là mã cũ để đối chiếu. “Tham khảo” ghi cách Tern và TravelJoy làm, kèm link nguồn; “không công bố” nghĩa là nguồn công khai không nói tới.

**Từ ngữ**
- Add-on: phần trả thêm, bật riêng ngoài gói.
- API: cổng kết nối để hai phần mềm trao đổi dữ liệu.
- Issue: một phần việc lập trình, khoảng 1–3 ngày.
- Lịch khởi hành, allotment: ngày khởi hành cố định và số chỗ AA giữ sẵn cho mỗi ngày.
- DPA: thoả thuận xử lý dữ liệu, phụ lục của hợp đồng đối tác.
- Sub-processor: bên thứ ba xử lý dữ liệu thay AA, phải ghi tên trong DPA.
- PCI: chuẩn bảo mật bắt buộc khi lưu số thẻ.
- 2FA, đăng nhập hai bước: sau mật khẩu, nhập thêm mã hoặc xác nhận trên điện thoại.
- Passkey: đăng nhập bằng vân tay hoặc khuôn mặt trên điện thoại.
- Owner / agent / assistant: chủ đại lý / nhân viên bán hàng / trợ lý.
- Workflow: chuỗi việc chạy tự động, ví dụ gửi email chúc mừng sinh nhật.
- Stripe Connect: tài khoản nền tảng của Stripe, cho phép nối Stripe của từng đại lý.
- Tech Provider: tư cách đối tác kỹ thuật Meta cấp, cần để nối WhatsApp cho đại lý.
- CASA: đợt kiểm định bảo mật hằng năm Google đòi khi app đọc hộp thư Gmail.
- ACH: chuyển khoản ngân hàng ở Mỹ.
- SaaS: phần mềm thuê theo tháng qua mạng.

---

## 1. Giá và mô hình kinh doanh

### 1.1 Gói giá và phần trả thêm cho đại lý [Q1.1, R11]
**Bối cảnh:** Spec §1 ghi CRM “miễn phí cho đối tác”; §11 gap 8 chưa có mô hình giá. Câu này gộp R11 (comparison.md §5), crm-v2.2 §9 Q8 và market-travel-crm §9 Q2. Chi phí AA ước ≈ $8–9/đại lý/tháng ở mức 10 đại lý, chưa tính ký điện tử (ước tính 20/10/2026). Mọi lựa chọn dưới đây: đại lý tự trả phí bên thứ ba (WhatsApp, SMS, phí thẻ).

**Tham khảo:**
- Tern: thu theo ghế, $49/ghế/tháng nếu trả tháng, $35 nếu trả quý hoặc năm; add-on Tern Pro $19–$149/tháng cho thêm AI; không tính theo số trip hay doanh số; lấy 0,6% trên phí dịch vụ đi qua Stripe. ([giá](https://tern.travel/pricing), [Tern Pro](https://help.tern.travel/en/articles/15292346-tern-pro), [phí dịch vụ](https://help.tern.travel/en/articles/8866875-professional-service-fees))
- TravelJoy: Starter $19/tháng (tối đa 12 trip/năm), Pro $39/tháng ($32 nếu trả năm), Premium $79–$99/tháng; add-on SMS $49, email không giới hạn $29, Zapier $29, Copilot x10 $49 mỗi tháng; phí thẻ 3,5% + 30c, ACH 1,5% (Starter: thẻ 5% + 30c, ACH 3%); không gói nào tính theo doanh số. ([giá](https://traveljoy.com/pricing), [Premium](https://traveljoy.com/premium.html))
- Safari Portal (cho lựa chọn c): phí nền tảng 0,5% trên khoản khách thanh toán qua cổng. ([cổng thanh toán](https://help.safariportal.app/en/articles/20631-choosing-your-preferred-payment-processors-in))

**Lựa chọn:**
- a) Phần chính miễn phí ở mọi gói tenant portal; gói cao hoặc add-on trả phí cho AI soạn nháp, báo cáo đầy đủ, nhiều người dùng, chiến dịch email (2.2), đặt tour đoàn (2.1). **← đề xuất**
- b) Miễn phí toàn bộ như spec; AA chỉ sống bằng biên lợi nhuận tour AA.
- c) Thu phí nền tảng theo % giá trị booking (kiểu Safari Portal 0,5%); AA phải thấy số trip và doanh số của đại lý.
- d) Thu theo số người dùng (ghế) như Tern.

**Lý do đề xuất:** Tern và TravelJoy không lấy % doanh số (chỉ lấy phí trên khoản thanh toán qua cổng: Tern 0,6%, TravelJoy phí thẻ); AA không cần xem doanh số của đại lý.

### 1.2 Giá net cho đại lý [Q1.2, H9]
**Bối cảnh:** API tồn kho AA trả giá net cho CRM (spec §9 AA inventory API); báo giá ở module 6.

**Tham khảo:** không áp dụng (Tern và TravelJoy không bán tour của chính họ).

**Lựa chọn:**
- a) Dùng bảng giá net B2B đang có (biên 15%); đại lý tự đặt giá bán cho khách của họ. **← đề xuất**
- b) Lập bảng giá net riêng cho đại lý dùng CRM.
- c) Giá net theo hạng đại lý (theo khối lượng bán).

**Lý do đề xuất:** bảng giá đã có sẵn, không phải duy trì thêm bảng thứ hai.

### 1.3 Cách AA thu tiền đại lý khi đại lý bán tour AA [Q1.3]
**Bối cảnh:** Đã quyết AA xuất hoá đơn cho đại lý. Còn thiếu: trả trước hay công nợ, % cọc, tiền tệ hoá đơn, phí thẻ 3% có áp cho chuyển khoản không (spec module 6, 7; §11 gap 6: AUD/USD/VND/EUR).

**Tham khảo:** không áp dụng (Tern và TravelJoy không bán tour của chính họ).

**Lựa chọn:**
- a) Dùng đúng điều khoản B2B AA đang áp cho đại lý hiện tại (công nợ, cọc, tiền tệ, phí thẻ như hiện nay). **← đề xuất**
- b) Đại lý trả trước 100% trước ngày khởi hành, không công nợ.
- c) Cọc khi xác nhận, phần còn lại trước ngày khởi hành, theo điều khoản mới (ghi: % cọc, hạn trả, tiền tệ hoá đơn, phí thẻ có áp cho chuyển khoản không).

**Lý do đề xuất:** không tạo thêm một quy trình thu tiền thứ hai cho cùng một loại khách B2B.

### 1.4 Báo giá thấp hơn giá “từ …” công khai của AA [Q1.4]
**Bối cảnh:** Đại lý tự đặt giá bán (module 3). Ràng buộc giá nằm trong hợp đồng đối tác (spec §10 Non-code track phase 1).

**Tham khảo:** không áp dụng (Tern và TravelJoy không bán tour của chính họ).

**Lựa chọn:**
- a) Chỉ ghi trong hợp đồng đối tác; CRM cảnh báo, không chặn. **← đề xuất**
- b) CRM chặn mọi báo giá thấp hơn giá công khai.
- c) Không ràng buộc.

**Lý do đề xuất:** đại lý giữ quyền đặt giá, AA vẫn có căn cứ trong hợp đồng.

### 1.5 Người nhập giá net nhà cung cấp và bảng giá tour [Q1.5]
**Bối cảnh:** Báo giá tự động (module 3) cần giá thật trong AA-Booking (spec §9 AA inventory API). Trên Dev hiện dùng giá giả.

**Tham khảo:** không áp dụng (Tern và TravelJoy không bán tour của chính họ).

**Lựa chọn:**
- a) Đội ops/sản phẩm hiện tại nhập, xong trước khi chọn 3–5 đại lý thử nghiệm (ghi tên người phụ trách). **← đề xuất**
- b) Nhập dần từng tour khi đại lý hỏi tới.
- c) Chưa nhập; Dev dùng giá giả tới khi đủ 23 module, sau đó mới tính.

**Lý do đề xuất:** đại lý thật dùng báo giá tự động ngay từ ngày đầu, nên giá phải có trước.

---

## 2. Sản phẩm cho đại lý

### 2.1 Đặt tour theo đoàn [R12]
**Bối cảnh:** Đại lý bán tour ghép đoàn có lịch khởi hành cố định: một link gồm lịch trình, form và cọc; mỗi nhóm khách một trip; xếp phòng; chặn khi hết chỗ. Module mới khoảng 5–7 issue, dùng lịch khởi hành và số chỗ giữ sẵn (allotment) có trong AA-Booking (comparison.md §5 R12; spec module 3, 7; §9). Có thể là add-on (1.1).

**Tham khảo:**
- Tern: trip mẹ chứa lịch trình mẫu, trang đích và form tự đăng ký; mỗi nhóm khách thành một trip con có lịch thanh toán riêng; chọn phòng, quản lý số phòng còn lại; đồng bộ thay đổi từ trip mẹ (đang thử nghiệm, 09/2026). ([hướng dẫn](https://help.tern.travel/en/articles/10059452-a-guide-to-group-trip-functionality), [đồng bộ](https://help.tern.travel/en/articles/15445464-group-trip-syncing))
- TravelJoy: một link gồm lịch trình, form và cọc; giá theo phòng đơn/đôi, giới hạn số lượng, tự hiện hết chỗ, tự nhắc trả nốt; chỉ có từ gói Pro ($39/tháng). ([blog](https://traveljoy.com/blog/post/how-to-book-group-travel-like-a-pro-traveljoys-first-groups-workshop), [giá](https://traveljoy.com/pricing))

**Lựa chọn:**
- a) Có, làm sau khi đủ 23 module, dùng lịch khởi hành và số chỗ giữ sẵn của AA-Booking, nằm ở gói cao/add-on theo 1.1. **← đề xuất**
- b) Có, sau 23 module, miễn phí ở mọi gói.
- c) Không làm.

**Lý do đề xuất:** TravelJoy dùng tính năng này để kéo đại lý lên gói trả phí; AA chặn hết chỗ được bằng tồn kho thật.

### 2.2 Chiến dịch email cho khách của đại lý [R14]
**Bối cảnh:** Đại lý gửi email hàng loạt cho khách của chính họ, chỉ người đã đồng ý nhận, có nút huỷ đăng ký. AA vẫn không bao giờ gửi cho khách của đại lý (spec §2). Module mới khoảng 2–3 issue, phí gửi rất nhỏ (spec module 10; comparison.md §5 R14). Có thể là add-on (1.1).

**Tham khảo:**
- Tern: chưa mở gửi email hàng loạt cho mọi người; tính năng chiến dịch đang chỉ có cho một nhóm nhỏ người dùng; khuyên dùng công cụ email marketing riêng; có workflow chăm khách tự động gửi riêng từng người (sinh nhật, hộ chiếu sắp hết hạn, kỷ niệm). ([FAQ](https://help.tern.travel/en/articles/9528236-can-i-send-emails-to-multiple-recipients-at-once-like-a-marketing-email-campaign), [workflow](https://help.tern.travel/en/articles/11404393-contact-workflows-and-automations))
- TravelJoy: tab Marketing (02/2026) kéo thả, có quản lý huỷ đăng ký; Pro được 12 chiến dịch × 300 người/năm, không giới hạn +$29/tháng; không nói gì về xin đồng ý nhận. ([blog](https://traveljoy.com/blog/post/meet-your-new-marketing-tab), [Premium](https://traveljoy.com/premium.html))

**Lựa chọn:**
- a) Có: chỉ gửi khách đã đồng ý nhận marketing, kèm huỷ đăng ký, gửi bằng tên đại lý, có nội dung AA làm sẵn để đại lý chọn. **← đề xuất**
- b) Chỉ gửi riêng từng khách và nhắc tự động, không gửi hàng loạt (gần cách Tern đang làm với phần lớn người dùng).
- c) Không làm; đại lý dùng công cụ email riêng.

**Lý do đề xuất:** chặt hơn TravelJoy về đồng ý nhận, và nội dung AA làm sẵn là lợi thế riêng.

### 2.3 Mục “Trước khi đi” do AA viết sẵn [R38]
**Bối cảnh:** Trước Ngày 1 của lịch trình có mục chuẩn bị, điền sẵn từ nội dung AA (đồ mang theo, thể lực, độ cao; khoảng 10 gói theo loại hoạt động), hiện dưới thương hiệu đại lý (S246 R38; spec module 3, 4, 11). Liên quan bảo hiểm ở 5.1.

**Tham khảo:**
- Tern: mỗi trip có “ngày” Pre-travel trước Ngày 1, tự ẩn khi trống; nội dung do advisor nhập, Tern không viết sẵn lời khuyên visa hay bảo hiểm; AI soạn được hướng dẫn điểm đến theo ngày đi. ([pre-travel](https://help.tern.travel/en/articles/10002081-pre-travel-itinerary-section), [AI Assist](https://help.tern.travel/en/articles/11020414-ai-assist-destination-guides))
- TravelJoy: không công bố mục “trước khi đi” riêng; Copilot soạn được tiêu đề, giới thiệu và danh sách đồ mang theo; không công bố nội dung visa hay bảo hiểm viết sẵn. ([blog](https://traveljoy.com/blog/post/create-client-ready-itineraries-in-minutes-with-itinerary-copilot))

**Lựa chọn:**
- a) AA viết các gói chuẩn bị; visa chỉ đưa link cổng chính thức, không viết lời khuyên visa; bảo hiểm chỉ nhắc và trỏ sang giấy từ chối hoặc hãng ở 5.1; đại lý sửa được trước khi gửi. **← đề xuất**
- b) AA viết cả lời khuyên visa và bảo hiểm.
- c) Chỉ để khung trống, đại lý tự viết (như Tern).

**Lý do đề xuất:** AA không phải chịu trách nhiệm cho lời khuyên visa có thể lỗi thời; phần chuẩn bị tour là thế mạnh nội dung của AA.

### 2.4 Hỗ trợ và hướng dẫn đại lý mới [R43]
**Bối cảnh:** Quyết định nhân sự: người của AA đồng hành khi đại lý mới vào, giờ và kênh hỗ trợ, sau đó mới có bot trợ giúp (≈ $1–3/tháng, ước tính 21/10/2026) (S246 R43; spec §11 gap 5 Onboarding).

**Tham khảo:**
- Tern: bot AI Fin xử lý gần 2.000 hội thoại/tuần, tự giải quyết hơn 85%, vẫn có người thật qua cuộc gọi 1-1; agency lớn có kế hoạch triển khai riêng gồm chuyển dữ liệu và đào tạo. ([blog](https://www.tern.travel/blog/the-future-of-human-support.html), [agencies](https://www.tern.travel/agencies))
- TravelJoy: bot AI T.J. trả lời đầu tiên trong khung chat cho mọi gói, không giải quyết được thì chuyển người; live chat (Pro, Premium) trong giờ hành chính thứ Hai–thứ Sáu 10:00–18:00 giờ miền Đông Mỹ; cuộc gọi đặt lịch; workshop trực tuyến 30 phút hằng tuần; Premium có hỗ trợ và đào tạo riêng. ([hỗ trợ](https://help.traveljoy.com/hc/en-us/articles/360016023172-How-to-reach-TravelJoy-support), [workshop](https://traveljoy.com/blog/post/traveljoy-training-workshops))

**Lựa chọn:**
- a) Thí điểm: một người AA đồng hành mỗi đại lý; email + WhatsApp trong giờ hành chính VN; đại lý tự chạy import (AA không chạm file khách); bot chỉ đọc trang trợ giúp, làm sau khi có đại lý thật (ghi tên người đồng hành). **← đề xuất**
- b) Chỉ trang trợ giúp và email, không có người đồng hành.
- c) Có người đồng hành và AA import giúp dữ liệu khách (nhân viên AA phải mở file khách).

**Lý do đề xuất:** cả hai đối thủ dùng bot trả lời trước rồi chuyển người. AA chưa có đại lý thật nên chưa có câu hỏi lặp lại cho bot học; bắt đầu bằng người, giữ lời hứa không chạm dữ liệu khách.

### 2.5 Báo đổi giờ bay của khách [R44]
**Bối cảnh:** Báo cho đại lý và AA ops khi chuyến bay đến hoặc đi của khách đổi giờ, không báo khách (S246 R44; spec §5 Stage 3; module 8, 10, 11). Giá API trạng thái chuyến bay chưa kiểm. Ghi thêm: đã từng lỡ đón vì đổi giờ bay chưa (có/không).

**Tham khảo:**
- Tern: theo dõi chuyến bay nhập theo số hiệu (dữ liệu FlightStats) từ 72 giờ trước giờ bay; đổi lịch thì email advisor, trễ hoặc huỷ thì báo cả khách; chuyến nhập tay không được theo dõi. ([thông báo](https://help.tern.travel/en/articles/9709513-how-does-tern-notify-my-client-when-their-flight-schedule-changes), [nhập tay](https://help.tern.travel/en/articles/9709532-does-tern-send-flight-notifications-for-manually-added-flights))
- TravelJoy: không công bố tính năng báo đổi giờ bay; Host Agency Reviews có ghi “Live Flight Database” nhưng không mô tả. ([HAR](https://hostagencyreviews.com/travel-agency-software/traveljoy))

**Lựa chọn:**
- a) Bước 1 ($0): việc nhắc 48 giờ trước giờ bay “xác nhận chuyến bay đến”, kèm link xem trạng thái; chỉ mua API trả phí khi ops báo có lỡ đón thật, và nêu giá để duyệt trước khi bật. **← đề xuất**
- b) Mua API trạng thái chuyến bay ngay khi có đại lý thật.
- c) Không làm.

**Lý do đề xuất:** chi phí $0 cho tới khi có bằng chứng lỡ đón thật.

### 2.6 Tên miền và địa chỉ email khách nhìn thấy [Q2.8]
**Bối cảnh:** Trang và form cho khách (spec module 1, 11) và email gửi đi (§9 Gmail/Outlook send-as). Dev đang dùng tên miền thử. Mua tên miền mới thường vài chục USD/năm (ước tính 20/10/2026).

**Tham khảo:**
- Tern: email đi từ hộp thư Google/Microsoft của advisor; một số email hệ thống mang tên “Tên doanh nghiệp via Tern”; không công bố tên miền riêng cho trang khách. ([email](https://help.tern.travel/en/articles/13976544-which-emails-come-from-you-and-which-come-from-tern))
- TravelJoy: email gửi đi từ Gmail, Microsoft hoặc địa chỉ email trên tên miền riêng của đại lý (cài DNS), hoặc dịch vụ gửi của TravelJoy; không công bố tên miền riêng cho trang và form của khách. ([Gmail](https://help.traveljoy.com/hc/en-us/articles/360028239552-Connect-your-Google-Mail-account-to-TravelJoy), [email doanh nghiệp](https://help.traveljoy.com/hc/en-us/articles/360030721131-Help-clients-recognize-your-messages-by-connecting-your-business-email-account-to-TravelJoy))

**Lựa chọn:**
- a) Một tên miền trung tính cho sản phẩm; đại lý nào muốn thì tự cài tên miền riêng; email gửi từ hộp thư của đại lý. **← đề xuất**
- b) Một tên miền chung mang tên AA.
- c) Chỉ dùng tên miền riêng của từng đại lý.

**Lý do đề xuất:** khách thấy thương hiệu đại lý; tên miền riêng cho trang khách là điểm đối thủ chưa công bố.

### 2.7 Zalo cho khách Việt Nam (cần xác nhận) [H7]
**Bối cảnh:** Đã có câu trả lời tạm: bản đầu chưa làm Zalo. Spec chỉ ghi WhatsApp, SMS, Messenger, Instagram (§7 Conversation.channel; module 9).

**Tham khảo:**
- Tern: không có Zalo; không có WhatsApp hay SMS gửi khách; advisor và khách chat trong app của khách. ([email/tin nhắn](https://help.tern.travel/en/articles/13976544-which-emails-come-from-you-and-which-come-from-tern))
- TravelJoy: không có Zalo; chỉ có SMS (add-on $49/tháng). ([Premium](https://traveljoy.com/premium.html))

**Lựa chọn:**
- a) Bản đầu không có Zalo; xem lại khi có đại lý VN dùng dữ liệu thật. **← đề xuất (xác nhận)**
- b) Có Zalo ngay trong bản đầu.

**Lý do đề xuất:** chưa có đại lý VN dùng dữ liệu thật trong giai đoạn đầu.

---

## 3. Pháp lý và dữ liệu

### 3.1 Pháp nhân ký hợp đồng với đại lý [Q2.1, H5]
**Bối cảnh:** Hợp đồng đối tác và DPA (spec §10 Non-code track phase 0–1). Cùng pháp nhân này đứng tên tài khoản Meta (4.2), Stripe (4.5), Google (4.7). Thời điểm thuê luật sư hỏi riêng ở 3.2.

**Tham khảo:** không áp dụng (việc nội bộ của AA).

**Lựa chọn:**
- a) Pháp nhân AA đang dùng cho hợp đồng đối tác (ghi tên); dùng mẫu DPA đã soạn. **← đề xuất**
- b) Dùng một pháp nhân khác cho sản phẩm CRM (ghi tên).

**Lý do đề xuất:** dùng lại pháp nhân và mẫu đã có.

### 3.2 Thời điểm thuê luật sư [Q3.9]
**Bối cảnh:** Luật sư xem luật dữ liệu VN, EU, Úc, hợp đồng đối tác và waiver (spec §10 Non-code track phase 0). Chưa có báo giá.

**Tham khảo:** không áp dụng (việc nội bộ của AA).

**Lựa chọn:**
- a) Gửi bản tóm tắt cho luật sư khi chạm một trong ba mốc: đại lý VN/EU muốn dùng dữ liệu thật; có đại lý thứ 6; 60 ngày sau khách thật đầu tiên. **← đề xuất**
- b) Thuê ngay bây giờ.
- c) Thuê trước khi mở cho 3–5 đại lý thử nghiệm.

**Lý do đề xuất:** chi phí luật sư đi cùng rủi ro thật, không trả khi mới có dữ liệu giả.

### 3.3 Lời hứa quyền riêng tư với đại lý [Q2.2, H3]
**Bối cảnh:** Spec F1 hứa không ai ngoài đại lý xem được dữ liệu, kể cả AA (§8). AA sở hữu tài khoản máy chủ nên khẩn cấp vẫn mở được. Câu trả lời tạm trước đây là câu ở lựa chọn b; lựa chọn a là câu đề xuất mới thay thế, theo mô hình 3 lớp (crm-v2.2 §3, §9 Q9).

**Tham khảo:**
- Tern: mã hoá thêm một lớp cho dữ liệu và ảnh hộ chiếu; không công bố lời hứa về việc nhân viên Tern mở hồ sơ khách; privacy policy (19/12/2025) chỉ hứa “reasonable safeguards”. ([bảo mật](https://help.tern.travel/en/articles/8126635-data-privacy-and-security-in-tern), [privacy](https://www.tern.travel/privacy))
- TravelJoy: không công bố lời hứa tương tự; privacy policy (29/05/2026) chỉ hứa bảo vệ khỏi truy cập trái phép; có 2FA, PCI có audit (theo Host Agency Reviews). ([privacy](https://traveljoy.com/privacy), [HAR](https://hostagencyreviews.com/travel-agency-software/traveljoy))

**Lựa chọn:**
- a) Câu hứa mới: “AA quản lý tài khoản đại lý mà không xem hồ sơ khách. Nhân viên AA chỉ xem được dữ liệu khi chủ đại lý tự cấp quyền hỗ trợ có thời hạn, mặc định chỉ đọc và ẩn thông tin danh tính khách. Khẩn cấp về an ninh hoặc pháp lý thì AA có thể mở dữ liệu của một đại lý, phải đăng nhập hai bước, và việc đó tự hiện trong nhật ký của đại lý.” **← đề xuất**
- b) Giữ câu trả lời tạm trước đây: “nhân viên AA không mở được hồ sơ khách” (không đúng hoàn toàn về kỹ thuật).
- c) Không đưa lời hứa riêng; chỉ dùng chính sách quyền riêng tư chung.

**Lý do đề xuất:** nói đúng sự thật về trường hợp khẩn cấp, và vẫn cao hơn mọi đối thủ đang công bố.

### 3.4 Điều khoản truy cập khẩn cấp (break-glass) [V22-Q5]
**Bối cảnh:** Đi cùng câu 3.3 (spec §8 AA access; F5; crm-v2.2 §3 lớp 3, §9 Q5). Đội kỹ thuật hiện chỉ có một người nhận báo động; cần người thứ hai.

**Tham khảo:**
- Tern, TravelJoy: không công bố điều khoản truy cập khẩn cấp của nhân viên nhà cung cấp. ([Tern privacy](https://www.tern.travel/privacy), [TravelJoy privacy](https://traveljoy.com/privacy))
- Phần mềm SaaS khác: Zendesk có quyền vào tài khoản khách “không báo trước” khi khẩn cấp hoặc nghi vi phạm điều khoản ([Zendesk](https://support.zendesk.com/hc/en-us/articles/4408824477082)); Atlassian chỉ vào dữ liệu khi khách cấp quyền ([Atlassian](https://support.atlassian.com/atlassian-cloud/kb/atlassian-cloud-support-data-access-request-faq/)).

**Lựa chọn:**
- a) Có điều khoản: chỉ khi khẩn cấp an ninh/pháp lý; đăng nhập hai bước; tối đa 1 giờ; mỗi lần một đại lý; tự hiện ngay trong nhật ký đại lý; email báo chủ đại lý trong 24 giờ. Chỉ định người thứ hai nhận báo động (ghi tên). **← đề xuất**
- b) Như a, nhưng báo chủ đại lý trong 72 giờ.
- c) Không có điều khoản; mọi lần mở đều phải xin đại lý đồng ý trước, kể cả khẩn cấp.

**Lý do đề xuất:** có quyền khẩn cấp như Zendesk nhưng báo đại lý rõ hơn; khớp lời hứa 3.3.

### 3.5 Quyền xem hỗ trợ của AA và thời hạn mặc định [Q2.3]
**Bối cảnh:** Nhân viên AA xem CRM của đại lý để hỗ trợ (spec §8 AA access; F5; crm-v2.2 §3 lớp 2, §9 Q4). Gộp market-travel-crm §9 Q4: có ghi vào hợp đồng/DPA rằng AA chỉ thấy danh tính khách trong phiên đại lý cấp không.

**Tham khảo:**
- Tern: không công bố việc nhân viên Tern vào tài khoản advisor hay thời hạn; “emergency trip access” là quyền của quản lý agency, không phải của Tern; không có DPA công khai. ([agencies](https://www.tern.travel/agencies), [privacy](https://www.tern.travel/privacy))
- TravelJoy: không công bố; không có DPA công khai; hỗ trợ qua email, chat và cuộc gọi đặt lịch. ([privacy](https://traveljoy.com/privacy), [hỗ trợ](https://help.traveljoy.com/hc/en-us/articles/360016023172-How-to-reach-TravelJoy-support))

**Lựa chọn:**
- a) Chỉ khi chủ đại lý tự bật; mặc định 24 giờ, chỉ đọc, ẩn danh tính khách; mọi lần xem ghi nhật ký; tắt được bất cứ lúc nào; ghi vào hợp đồng và DPA. **← đề xuất**
- b) Như a, mặc định 7 ngày.
- c) Như a, mặc định 14 ngày.
- d) Không cho nhân viên AA xem vào CRM của đại lý.

**Lý do đề xuất:** thời hạn ngắn nhất đủ cho một lần hỗ trợ; ghi vào DPA là điểm mà cả hai đối thủ không có.

### 3.6 Khoá mã hoá riêng của đại lý (BYOK) [V22-Q3]
**Bối cảnh:** Spec F1 ghi “mã hoá bằng khoá của chính đại lý” (§8). Thiết kế hiện tại: một khoá chính mỗi môi trường và một khoá dữ liệu riêng mỗi đại lý (crm-v2.2 §2 S1, §9 Q3).

**Tham khảo:**
- Tern: mã hoá thêm một lớp cho dữ liệu hộ chiếu; không công bố khoá riêng cho từng agency. ([bảo mật](https://help.tern.travel/en/articles/8126635-data-privacy-and-security-in-tern))
- TravelJoy: không công bố. ([privacy](https://traveljoy.com/privacy))
- Phần mềm SaaS khác: Atlassian dùng khoá chung cho các khách, gắn mã riêng từng khách; bộ khoá riêng mỗi khách (CMK) là tuỳ chọn thêm ở gói cao. ([Atlassian CMK](https://support.atlassian.com/security-and-access-policies/docs/what-is-cmk-encryption/))

**Lựa chọn:**
- a) Bản đầu dùng thiết kế hiện tại; khoá riêng do đại lý giữ là tuỳ chọn trả phí sau, chỉ làm khi có đại lý hỏi; sửa câu chữ F1 trong spec và DPA cho khớp (cùng quyết định với 3.3). **← đề xuất**
- b) Mỗi đại lý có khoá riêng do đại lý giữ, ngay từ đại lý đầu tiên.

**Lý do đề xuất:** đại lý nhỏ hiếm khi cần; Atlassian cũng để khoá riêng là tuỳ chọn thêm.

### 3.7 Lời hứa khi xoá dữ liệu [Q2.4]
**Bối cảnh:** Xoá có kiểm chứng (spec module 18; §8 Agency controls). Do dùng một khoá chính mỗi môi trường, thời hạn xoá gắn với thời hạn bản sao lưu (crm-v2.2 §9 Q2).

**Tham khảo:**
- Tern: xoá theo yêu cầu, có thể giữ một phần vì lý do pháp lý; khách của advisor phải hỏi advisor; không công bố thời hạn backup; không có xoá có kiểm chứng. ([privacy](https://www.tern.travel/privacy), [xuất CSV](https://help.tern.travel/en/articles/14795473-exporting-contacts-with-passport-data-to-csv))
- TravelJoy: có quyền yêu cầu xoá và xuất dữ liệu; giữ dữ liệu “as long as necessary”; không công bố thời hạn backup hay xác nhận xoá. ([privacy](https://traveljoy.com/privacy))

**Lựa chọn:**
- a) “Xoá ngay trong ứng dụng. Không đọc lại được ở bất kỳ đâu, kể cả bản sao lưu, trong vòng tối đa 30 ngày.” **← đề xuất**
- b) Chỉ hứa xoá trong ứng dụng, không nhắc bản sao lưu (như Tern, TravelJoy).
- c) Thời hạn khác (ghi số ngày).

**Lý do đề xuất:** cụ thể và kiểm chứng được, rõ hơn mọi đối thủ.

### 3.8 Thời gian giữ nhật ký “ai đã xem gì” [Q2.5]
**Bối cảnh:** Nhật ký truy cập (spec module F5; crm-v2.2 §2 S2, §9 Q1). Chế độ lưu khoá vĩnh viễn không rút ngắn được sau khi bật; Dev chạy chế độ còn sửa được tới khi có câu trả lời.

**Tham khảo:**
- Tern: nhật ký hoạt động của trip chỉ đọc, không khôi phục; không công bố thời gian giữ. ([versioning](https://help.tern.travel/en/articles/8114228-trip-versioning-on-itineraries))
- TravelJoy: nhật ký form ghi lúc gửi, mở, ký kèm IP (03/2025); không công bố thời gian giữ. ([blog 03/2025](https://traveljoy.com/blog/post/traveljoy-travel-agency-software-updates-feb-2025))

**Lựa chọn:**
- a) Đại lý xem được 12 tháng; sau đó lưu khoá, không sửa được, thêm 6 năm trừ khi luật sư khuyên khác; đại lý tải được bản sao; chưa gửi liên tục sang hệ thống khác của đại lý. **← đề xuất**
- b) Giữ 12 tháng rồi xoá.
- c) Thời hạn khác (ghi số năm).

**Lý do đề xuất:** đủ dài cho tranh chấp và kiểm tra, chi phí lưu trữ nhỏ.

### 3.9 Báo đại lý khi AA ops xem thông tin khách [Q2.6]
**Bối cảnh:** Khi chuyến đã chốt, AA ops nhận thông tin khách để vận hành tour (spec module 8; F5).

**Tham khảo:**
- Tern: quản lý agency có “emergency trip access” vào trip của advisor; không công bố việc báo advisor khi có người xem. ([agencies](https://www.tern.travel/agencies))
- TravelJoy: không công bố. ([privacy](https://traveljoy.com/privacy))

**Lựa chọn:**
- a) Có: nhật ký đại lý hiện dòng “AA ops đã xem thông tin chuyến X ngày Y”. **← đề xuất**
- b) Không báo.

**Lý do đề xuất:** minh bạch và khớp lời hứa 3.3.

### 3.10 Thông tin khách AA ops gửi cho khách sạn, xe [Q2.7]
**Bối cảnh:** Dữ liệu ops xoá 90 ngày sau chuyến (spec module 8; §8), nhưng bản đã gửi cho nhà cung cấp nằm ngoài hệ thống, không tự xoá được.

**Tham khảo:** không áp dụng (Tern và TravelJoy không vận hành tour).

**Lựa chọn:**
- a) Chỉ gửi họ tên, số người, yêu cầu ăn uống/đi lại; không gửi số hộ chiếu trừ khi nhà cung cấp bắt buộc; mỗi lần xuất danh sách đều ghi nhật ký. **← đề xuất**
- b) Gửi đầy đủ thông tin như cách làm hiện nay.

**Lý do đề xuất:** gửi ít nhất có thể vì bản gửi đi không thu hồi được.

### 3.11 Dịch vụ AI ở tài khoản máy chủ thứ hai của AA [Q2.10]
**Bối cảnh:** Phần AI soạn nháp (spec module 14; §9 LLM provider, không lưu dữ liệu) chạy ở một tài khoản máy chủ AA mua qua eCloudvalley.

**Tham khảo:**
- Tern: số hộ chiếu đầy đủ không bao giờ gửi cho mô hình AI; không tìm thấy danh sách bên xử lý AI công khai. ([AI chat](https://help.tern.travel/en/articles/14182386-ai-chat-for-notes-and-crm))
- TravelJoy: không dùng dữ liệu đại lý và khách để huấn luyện mô hình AI công khai; không tìm thấy danh sách bên xử lý AI công khai. ([AI](https://traveljoy.com/ai.html))

**Lựa chọn:**
- a) Đồng ý; ghi tài khoản này vào danh sách bên xử lý dữ liệu (sub-processor) trong DPA. **← đề xuất**
- b) Không đồng ý; tắt phần AI tới khi có cách khác.

**Lý do đề xuất:** minh bạch với đại lý mà vẫn giữ được phần AI.

### 3.12 Số liệu tổng hợp AA được xem (cần xác nhận) [H11]
**Bối cảnh:** Đã có câu trả lời tạm. AA chỉ xem số liệu tổng hợp, không xem từng khách (spec module 17; §8 AA access).

**Tham khảo:**
- Tern, TravelJoy: không công bố quy tắc tổng hợp số liệu từ nhiều đại lý. ([Tern privacy](https://www.tern.travel/privacy), [TravelJoy privacy](https://traveljoy.com/privacy))

**Lựa chọn:**
- a) Chỉ nhóm có ít nhất 10 khách, từ ít nhất 3 đại lý, và chỉ của đại lý tự chọn tham gia. **← đề xuất (xác nhận)**
- b) Ngưỡng khác (ghi số khách, số đại lý).

**Lý do đề xuất:** không suy ra được một khách hay một đại lý cụ thể.

### 3.13 Đăng nhập hai bước cho nhân viên đại lý [Q2.9]
**Bối cảnh:** Chủ đại lý (owner) và nhân viên bán hàng (agent) xem được số hộ chiếu (spec module F4, F1).

**Tham khảo:**
- Tern: 2FA qua SMS, app xác thực hoặc passkey; bắt buộc để dùng uỷ quyền thẻ; không công bố bắt buộc cho mọi người dùng. ([bảo mật](https://help.tern.travel/en/collections/5447672-security-and-data), [uỷ quyền thẻ](https://help.tern.travel/en/articles/12176225-payments-authorizations-in-tern))
- TravelJoy: có 2FA khi đăng nhập (theo Host Agency Reviews); phương thức và việc bắt buộc không công bố. ([HAR](https://hostagencyreviews.com/travel-agency-software/traveljoy))

**Lựa chọn:**
- a) Bắt buộc bước hai cho owner và agent: passkey trên điện thoại hoặc app xác thực; lần đầu thêm khoảng 1 phút. **← đề xuất**
- b) Có nhưng không bắt buộc.
- c) Bắt buộc cho mọi vai trò, kể cả trợ lý (assistant).

**Lý do đề xuất:** Tern đã bắt buộc 2FA cho tính năng nhạy cảm và đại lý vẫn dùng.

### 3.14 Chứng chỉ bảo mật SOC 2 / ISO 27001 [MKT-Q7]
**Bối cảnh:** Có đại lý hoặc hãng bảo hiểm đòi chứng chỉ không. Spec chỉ yêu cầu trang dữ liệu công khai (§10 Non-code track phase 4).

**Tham khảo:**
- Tern: không công bố chứng chỉ của riêng mình; chỉ nói trung tâm dữ liệu có ISO 27001, SOC 1/SOC 2, PCI Level 1. ([bảo mật](https://help.tern.travel/en/articles/8126635-data-privacy-and-security-in-tern))
- TravelJoy: không công bố SOC 2 hay ISO 27001; công bố PCI có audit bên thứ ba và tham gia EU-U.S. Data Privacy Framework. ([HAR](https://hostagencyreviews.com/travel-agency-software/traveljoy), [privacy](https://traveljoy.com/privacy))

**Lựa chọn:**
- a) Chưa làm chứng chỉ; công bố trang dữ liệu bằng ngôn ngữ thường và tài liệu bảo mật; hỏi lại khi phỏng vấn 3–5 đại lý thử nghiệm. **← đề xuất**
- b) Bắt đầu chuẩn bị SOC 2 ngay (có phí kiểm định hằng năm, chưa có báo giá).

**Lý do đề xuất:** cả hai đối thủ đều không công bố chứng chỉ riêng; chỉ làm khi một đại lý hoặc hãng bảo hiểm thật đòi.

---

## 4. Dịch vụ bên ngoài có phí

Các mục dưới đây chưa cần trả tiền: Dev dùng bản miễn phí hoặc bản test. Chỉ cần quyết trước khi có đại lý thật.

### 4.1 Ký điện tử cho điều khoản và waiver trekking [Q3.1, H12]
**Bối cảnh:** Spec module 12: khách ký điện tử, lưu PDF và nhật ký ký, hãng bảo hiểm chấp nhận; §9 không chỉ định hãng. Phụ thuộc câu trả lời của hãng bảo hiểm (5.1). Câu trả lời tạm trước đây là c (Documenso Teams); câu này hỏi lại vì có lựa chọn rẻ hơn. Lựa chọn đắt hơn, không đề xuất: Documenso Platform $250/tháng nếu trả năm ($3.000/năm), Dropbox Sign API từ $75/tháng (giá xem 20/10/2026).

**Tham khảo:**
- Tern: khối ký trong form, đặt sau điều khoản, có dấu thời gian; không công bố nhà cung cấp ký điện tử bên ngoài. ([e-signature](https://help.tern.travel/en/articles/9670279-can-i-add-an-e-signature-to-my-forms))
- TravelJoy: form có chữ ký, nhật ký ghi lúc gửi, mở, ký kèm địa chỉ IP (03/2025); không công bố nhà cung cấp ký điện tử bên ngoài. ([blog 03/2025](https://traveljoy.com/blog/post/traveljoy-travel-agency-software-updates-feb-2025))

**Lựa chọn:**
- a) AA tự làm chữ ký điện tử đơn giản (mã qua email, gõ tên, bấm đồng ý, niêm phong PDF), ≈ $0–1/tháng, nếu hãng bảo hiểm chấp nhận. **← đề xuất**
- b) BoldSign API: từ $30/tháng gồm 40 lượt ký, thêm $0,75/lượt; có thương hiệu riêng.
- c) Documenso Teams: $40/tháng nếu trả năm ($480/năm; trả tháng ≈ $50), gồm 5 người dùng; trang ký có thể hiện chữ “Documenso”.
- d) Tự cài Documenso trên máy chủ AA: ≈ $5–17/tháng cộng chứng thư số (chưa rõ giá).

**Lý do đề xuất:** cả hai đối thủ đều tự làm chữ ký trong form; rẻ nhất và dữ liệu không ra ngoài. Nếu hãng bảo hiểm đòi nhà cung cấp có tên tuổi thì chọn b.

### 4.2 WhatsApp, Messenger, Instagram: đi qua ai [Q3.2]
**Bối cảnh:** Spec module 9 ghi Twilio/360dialog (§7 Conversation.channel; §10 phase 3). Đi thẳng với Meta cần đăng ký Tech Provider, xác minh doanh nghiệp, duyệt app (2–4 tuần trở lên), đứng tên pháp nhân ở 3.1. Gộp crm-v2.2 §9 Q7, Q11 và market-travel-crm §9 Q5. Kênh nào có lúc mở hỏi riêng ở 4.3.

**Tham khảo:**
- Tern: không có WhatsApp, SMS, Messenger hay Instagram; advisor và khách chat trong app của khách. ([email/tin nhắn](https://help.tern.travel/en/articles/13976544-which-emails-come-from-you-and-which-come-from-tern))
- TravelJoy: không có WhatsApp, Messenger hay Instagram; chỉ SMS (add-on $49/tháng). ([Premium](https://traveljoy.com/premium.html))

**Lựa chọn:**
- a) Đi thẳng với Meta: AA $0, Meta tính phí tin vào thẻ của đại lý, mỗi đại lý sở hữu tài khoản WhatsApp Business của mình. **← đề xuất**
- b) Qua Twilio hoặc 360dialog như spec: thêm phí trung gian (Twilio +$0,005/tin cho đại lý, giá xem 20/10/2026).

**Lý do đề xuất:** rẻ nhất, và đại lý giữ tài khoản WhatsApp của chính họ.

### 4.3 WhatsApp, Messenger, Instagram: lúc mở có gì [Q3.2]
**Bối cảnh:** Kênh nhắn tin có sẵn khi mở cho đại lý thật (spec module 9; §10 phase 3). Không phụ thuộc lựa chọn ở 4.2.

**Tham khảo:**
- Tern: không có kênh nào trong ba kênh này. ([email/tin nhắn](https://help.tern.travel/en/articles/13976544-which-emails-come-from-you-and-which-come-from-tern))
- TravelJoy: không có kênh nào trong ba kênh này. ([Premium](https://traveljoy.com/premium.html))

**Lựa chọn:**
- a) WhatsApp nằm trong 23 module, có ngay khi mở cho đại lý thật; Messenger/Instagram làm sau 23 module. **← đề xuất**
- b) Cả ba kênh có ngay khi mở cho đại lý thật.
- c) Chỉ email lúc mở; WhatsApp làm sau khi có đại lý thật.

**Lý do đề xuất:** đối thủ không có kênh nào trong ba kênh, nên không có áp lực làm cả ba ngay.

### 4.4 SMS [Q3.3]
**Bối cảnh:** Gửi SMS cho khách qua Twilio (spec module 9; §9).

**Tham khảo:**
- Tern: không công bố SMS gửi khách; SMS chỉ thấy ở mã đăng nhập hai bước. ([bảo mật](https://help.tern.travel/en/collections/5447672-security-and-data))
- TravelJoy: bán SMS trọn gói $49/tháng cho 1.000 tin, kèm số điện thoại địa phương; đại lý không cần tài khoản Twilio. ([Premium](https://traveljoy.com/premium.html))

**Lựa chọn:**
- a) Mỗi đại lý dùng tài khoản Twilio của chính họ và tự trả; AA $0. **← đề xuất**
- b) AA bán SMS trọn gói như TravelJoy (AA trả Twilio, thu đại lý theo gói).
- c) Không làm SMS.

**Lý do đề xuất:** AA không gánh phí; có thể chuyển sang b sau nếu đại lý nhỏ thấy khó.

### 4.5 Thanh toán thẻ qua Stripe [Q3.4]
**Bối cảnh:** Khách trả cọc và trả nốt qua link, tiền vào thẳng tài khoản Stripe của đại lý (spec module 7; §9 Stripe). CRM chỉ thu cọc và tiền khách trả đại lý; tiền đại lý trả nhà cung cấp hoặc AA đi ngoài CRM (theo 1.3). AA cần tài khoản nền tảng Stripe Connect đứng tên pháp nhân ở 3.1. Stripe không hoạt động ở VN. Gộp market-travel-crm §9 Q1.

**Tham khảo:**
- Tern: khách chỉ uỷ quyền thẻ, advisor tự charge qua nhà cung cấp; phí dịch vụ thu qua Stripe Connect của advisor, Tern lấy thêm 0,6%. ([uỷ quyền](https://help.tern.travel/en/articles/12176225-payments-authorizations-in-tern), [phí dịch vụ](https://help.tern.travel/en/articles/8866875-professional-service-fees))
- TravelJoy: thu thẻ/ACH vào ví của trip rồi trả nhà cung cấp; cũng có uỷ quyền thẻ, chuyển cho nhà cung cấp tự charge; phí thẻ 3,5% + 30c, ACH 1,5–3%. ([giá](https://traveljoy.com/pricing), [trả nhà cung cấp](https://help.traveljoy.com/hc/en-us/articles/9484158141076-Pay-your-suppliers))

**Lựa chọn:**
- a) Stripe cho đại lý ở nước có Stripe (ví dụ Úc, EU); AA $0, Stripe tính phí thẻ vào đại lý; không lưu thẻ để uỷ quyền; Dev dùng tài khoản test miễn phí. **← đề xuất**
- b) Như a, thêm lưu thẻ để uỷ quyền như Tern và TravelJoy (AA vào phạm vi PCI).
- c) Chưa làm thanh toán online; đại lý ghi tay khoản đã thu.

**Lý do đề xuất:** tiền đi thẳng vào tài khoản đại lý như Tern, và AA đứng ngoài phạm vi PCI.

### 4.6 Cổng thanh toán cho đại lý Việt Nam [Q3.5]
**Bối cảnh:** Cổng nội địa thay Stripe cho đại lý VN (spec module 7; §11 gap 6 VND). Chưa có báo giá.

**Tham khảo:**
- Tern, TravelJoy: không công bố cổng thanh toán cho Việt Nam. ([Tern uỷ quyền](https://help.tern.travel/en/articles/12176225-payments-authorizations-in-tern), [TravelJoy giá](https://traveljoy.com/pricing))

**Lựa chọn:**
- a) Chưa gấp: trong lúc chờ, đại lý VN ghi tay khoản đã thu; chọn vài cổng để xin báo giá khi có đại lý VN dùng dữ liệu thật (ghi tên cổng muốn hỏi). **← đề xuất**
- b) Xin báo giá ngay bây giờ.

**Lý do đề xuất:** đại lý VN chưa dùng dữ liệu thật trong giai đoạn đầu.

### 4.7 Gửi email bằng Gmail của đại lý [Q3.6]
**Bối cảnh:** Spec module 5 ghi đồng bộ Gmail/Outlook hai chiều và “đại lý bỏ hẳn Gmail” (§9). Chỉ xin quyền “gửi thư” thì tránh được kiểm định CASA hằng năm của Google (≈ $675–5.400/năm, tìm hiểu 20/10/2026; Google không công bố giá). Google xác minh app miễn phí, cần pháp nhân và tên miền có trang chủ, chính sách riêng tư. Gộp market-travel-crm §9 Q6.

**Tham khảo:**
- Tern: đồng bộ toàn bộ thư Google/Microsoft vào Tern; không công bố đã qua CASA. ([email](https://help.tern.travel/en/articles/9015404-an-introduction-to-email-in-tern))
- TravelJoy: chỉ gửi đi bằng Gmail của đại lý; không đồng bộ hộp thư. ([Gmail](https://help.traveljoy.com/hc/en-us/articles/360028239552-Connect-your-Google-Mail-account-to-TravelJoy))

**Lựa chọn:**
- a) Bản đầu: gửi đi từ Gmail đại lý, nhận thư qua địa chỉ chuyển tiếp/BCC; không đồng bộ hai chiều; $0. Ghi pháp nhân và tên miền để Google xác minh. **← đề xuất**
- b) Đồng bộ hai chiều ngay; cần kiểm định CASA hằng năm.

**Lý do đề xuất:** TravelJoy bán được chỉ với gửi đi; “bỏ hẳn Gmail” không phải điều kiện thị trường bắt buộc.

### 4.8 Gửi email bằng Outlook [Q3.7]
**Bối cảnh:** Như 4.7 cho đại lý dùng Outlook (spec module 5; §9). AA cần tài khoản tổ chức Microsoft 365 và vào chương trình đối tác miễn phí của Microsoft.

**Tham khảo:**
- Tern: kết nối hộp thư Google hoặc Microsoft (cần cấp cả quyền thư và lịch), thấy toàn bộ thư trong Tern. ([email](https://help.tern.travel/en/articles/9015404-an-introduction-to-email-in-tern))
- TravelJoy: gửi đi bằng tài khoản Microsoft (Office 365, Outlook); không công bố đồng bộ lịch. ([Gmail và Microsoft](https://help.traveljoy.com/hc/en-us/articles/360028239552-Connect-your-Google-Mail-account-to-TravelJoy))

**Lựa chọn:**
- a) Làm sau Gmail, khi có đại lý dùng Outlook; phí $0. **← đề xuất**
- b) Làm cùng lúc với Gmail.

**Lý do đề xuất:** chưa có đại lý thật; làm khi có nhu cầu. Lưu ý: cả hai đối thủ đều có Microsoft.

### 4.9 Tường lửa web cho trang khách [Q3.8]
**Bối cảnh:** Chặn tấn công và spam trên form và trang khách (spec module 1, 11; §11 gap 6). ≈ $7–8/tháng (ước tính 20/10/2026).

**Tham khảo:**
- Tern, TravelJoy: không công bố. ([Tern bảo mật](https://help.tern.travel/en/articles/8126635-data-privacy-and-security-in-tern), [TravelJoy privacy](https://traveljoy.com/privacy))

**Lựa chọn:**
- a) Bật khi có đại lý thật; AA chịu phí. **← đề xuất**
- b) Bật ngay trên Dev.
- c) Bật khi có đại lý thật; tính phí vào gói đại lý.

**Lý do đề xuất:** Dev không có dữ liệu thật; phí nhỏ.

---

## 5. Bảo hiểm và waiver

### 5.1 Hãng bảo hiểm duyệt waiver và bảo hiểm du lịch cho khách đại lý [Q4.1, H6, R13]
**Bối cảnh:** Spec §5 Stage 3 (bảo hiểm du lịch, waiver có ký), module 7, 12; §10 phase 2; comparison.md §5 R13. Câu trả lời của hãng quyết định 4.1. Giấy từ chối bảo hiểm có ký là 1 issue; báo giá bảo hiểm trong app là 3–5 issue. Hoa hồng hỏi riêng ở 5.2.

**Tham khảo:**
- Tern: báo giá trong app với Arch RoamRight, Chubb, Faye, Trawick, Travel Insured International; khách từ chối thì nhận email kèm biên nhận PDF, lưu vào tài liệu chuyến; có hoa hồng, tỷ lệ không công bố. ([từ chối bảo hiểm](https://help.tern.travel/en/articles/8857059-collecting-travel-insurance-authorization-opt-out), [Q1 2026](https://tern.travel/whats-new/q1-2026))
- TravelJoy: bán Faye (hoa hồng 24%) và Arch RoamRight (hoa hồng qua host agency); form có nhật ký gửi/mở/ký kèm IP; không công bố mẫu giấy từ chối bảo hiểm riêng. ([báo giá](https://traveljoy.com/blog/post/how-to-search-quote-and-book-on-traveljoy), [cập nhật](https://traveljoy.com/blog/post/product-updates-crm-groups-proposals-and-more), [blog 03/2025](https://traveljoy.com/blog/post/traveljoy-travel-agency-software-updates-feb-2025))

**Lựa chọn:**
- a) Nhờ hãng bảo hiểm AA đang dùng (ghi tên người liên hệ); hỏi cùng lúc: duyệt waiver, cách ký điện tử chấp nhận, có sản phẩm bảo hiểm du lịch cho khách đại lý kèm hoa hồng không. Bản đầu chỉ làm giấy từ chối bảo hiểm có ký. **← đề xuất**
- b) Như a, và làm báo giá bảo hiểm trong app ngay.
- c) Nhờ một hãng khác (ghi tên).

**Lý do đề xuất:** một lần hỏi giải quyết ba việc; các hãng tích hợp sẵn ở Tern/TravelJoy chủ yếu bán cho khách Mỹ, nên cần hỏi hãng của AA về khách AU/VN/EU.

### 5.2 Hoa hồng bảo hiểm du lịch [R13]
**Bối cảnh:** Nếu hãng ở 5.1 có sản phẩm cho khách đại lý kèm hoa hồng thì ai nhận (comparison.md §5 R13; spec module 7). Đại lý là bên bán cho khách; AA không xem doanh số của đại lý (1.1).

**Tham khảo:**
- Tern: advisor nhận hoa hồng trên mỗi chuyến, tỷ lệ không công bố. ([Q1 2026](https://tern.travel/whats-new/q1-2026))
- TravelJoy: advisor nhận 24% với Faye; Arch RoamRight trả qua host agency. ([báo giá](https://traveljoy.com/blog/post/how-to-search-quote-and-book-on-traveljoy), [cập nhật](https://traveljoy.com/blog/post/product-updates-crm-groups-proposals-and-more))

**Lựa chọn:**
- a) Đại lý hưởng toàn bộ hoa hồng. **← đề xuất**
- b) Chia hoa hồng giữa AA và đại lý (ghi tỷ lệ).
- c) Không nhận hoa hồng.

**Lý do đề xuất:** đại lý là bên bán, giống cách Tern và TravelJoy trả cho advisor; AA không phải theo dõi doanh số bảo hiểm của đại lý.

### 5.3 Mẫu điều khoản và waiver (cần xác nhận) [Q4.2, H10]
**Bối cảnh:** Đã có câu trả lời tạm (spec module 12; §10 Non-code track phase 2).

**Tham khảo:** không áp dụng (Tern và TravelJoy không bán tour của chính họ, nên không có mẫu waiver tour).

**Lựa chọn:**
- a) AA soạn mẫu song ngữ Anh–Việt từ điều khoản hiện tại; đội kinh doanh AA rà lại; hãng bảo hiểm duyệt. **← đề xuất (xác nhận)**
- b) Thuê luật sư soạn mẫu từ đầu.

**Lý do đề xuất:** dùng lại điều khoản đang chạy; luật sư chỉ cần khi chạm mốc ở 3.2.

---

## 6. Vận hành và thử nghiệm

### 6.1 Thời điểm bắt đầu thủ tục với Meta, Google, Microsoft [Q5.3]
**Bối cảnh:** Mỗi thủ tục mất vài tuần (spec §10 Non-code track phase 3); cần tên pháp nhân ở 3.1.

**Tham khảo:** không áp dụng (việc nội bộ của AA).

**Lựa chọn:**
- a) Bắt đầu khi đã chọn xong đại lý thật đầu tiên. **← đề xuất**
- b) Bắt đầu khoảng một tháng trước ngày mở dự kiến, để mở đúng ngày.

**Lý do đề xuất:** không tốn công khi chưa chắc ngày mở; nếu cần mở đúng ngày thì chọn b.

### 6.2 Xác nhận tour và người phụ trách lịch khởi hành (cần xác nhận) [Q5.4, H8]
**Bối cảnh:** Đã có câu trả lời tạm. Giữ chỗ và xác nhận qua API tồn kho AA (spec §9; module 3, 8). Còn thiếu tên người ở đội ops nhập lịch khởi hành và xác nhận tour theo yêu cầu.

**Tham khảo:** không áp dụng (Tern và TravelJoy không bán tour của chính họ).

**Lựa chọn:**
- a) Tour có lịch cố định tự xác nhận; tour khác “theo yêu cầu”, AA ops xác nhận trong 1 ngày làm việc; ghi tên người phụ trách. **← đề xuất (xác nhận)**
- b) Mọi tour đều do AA ops xác nhận tay.

**Lý do đề xuất:** đại lý có câu trả lời ngay cho tour cố định, ops chỉ xử lý phần cần người.

### 6.3 Khi chủ đại lý nghỉ hoặc mất tài khoản [V22-Q10]
**Bối cảnh:** Vai trò owner/agent/assistant (spec module F4; crm-v2.2 §3, §9 Q10). AA không tự gán chủ mới bằng một email lạ.

**Tham khảo:**
- Tern: vai trò Owner, Admin, Collaborator, Agent; chỉ Owner chuyển được quyền chủ; không công bố cách xử lý khi chủ mất tài khoản. ([vai trò](https://help.tern.travel/en/articles/9621179-what-is-the-difference-between-agency-roles-in-tern-owner-admin-collaborator-agent))
- TravelJoy: vai trò Owner, Team member, Assistant; không công bố cách chuyển quyền chủ. ([team](https://help.traveljoy.com/hc/en-us/articles/360028239792-Introduction-to-TravelJoy-teams-and-assistants))

**Lựa chọn:**
- a) AA chỉ thăng một người đã là thành viên của đại lý lên chủ, sau 14 ngày chờ, có email báo chủ cũ và ghi nhật ký; ghi vào hợp đồng đối tác. **← đề xuất**
- b) Như a, chờ 7 ngày.
- c) Như a, chờ 30 ngày.

**Lý do đề xuất:** đủ thời gian để chủ cũ phản đối, và chặn chiếm tài khoản bằng email giả.

---

## Đã quyết định (không cần trả lời)

- **H1:** làm đủ 23 module của spec trước; đại lý thật chỉ dùng sau đó. Ngày 30/11 trước đây chỉ là dự kiến, không còn là hạn chót.
- **H4 [Q5.1]:** trên Dev chỉ dùng đại lý giả, dữ liệu giả; mọi dịch vụ trả phí dùng bản test hoặc miễn phí, chưa phát sinh chi phí. Khi đủ 23 module (dự kiến giữa 12/2026 tới giữa 01/2027) sẽ chọn 3–5 đại lý thân quen ngoài EU và VN (ví dụ Úc), mỗi đại lý 30 phút phỏng vấn trước khi mở (spec §10 Pilot); câu chọn đại lý sẽ hỏi lúc đó.
- Các tính năng kỹ thuật từ so sánh Tern/TravelJoy và đợt ý tưởng 21/10 (R1–R10, R15–R44, trừ R38, R43, R44 ở mục 2) đưa thẳng vào thiết kế.
- R11 (giá, add-on) nằm ở 1.1; R12 ở 2.1; R13 (bảo hiểm du lịch) ở 5.1 và 5.2; R14 ở 2.2.
- AA không bao giờ gửi tin cho khách của đại lý (spec §2), kể cả khi có chiến dịch email ở 2.2.
