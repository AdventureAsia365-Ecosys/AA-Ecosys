# CRM cho đại lý: bảng hỏi quyết định kinh doanh và pháp lý (bản 2)

Bản 2 còn 12 câu: giá, người phụ trách, pháp nhân, luật sư, lời hứa với đại lý và những chỗ lệch chữ của spec `partner-crm-spec.md`. Các câu khác của bản trước đã có quyết định, liệt kê ở cuối trang.
4 câu cần chọn (2.1, 3.3, 4.1, 5.1): mỗi câu có 2–3 lựa chọn, lựa chọn đề xuất có ghi lý do; chọn một lựa chọn, hoặc ghi ý khác. 8 câu ghi “cần xác nhận” (1.1–1.4, 3.1, 3.2, 6.1, 6.2) đã có câu trả lời tạm là lựa chọn a: chỉ cần xác nhận và điền phần còn thiếu (tên người, tên pháp nhân, điều khoản B2B hiện tại); các lựa chọn ghi “Hoặc sửa” chỉ dùng khi muốn sửa.
Không có câu nào gấp: đại lý thật chỉ dùng sau khi đủ 23 module; trên Dev chỉ có đại lý giả, dữ liệu giả.

Ghi chú: nguồn công khai kiểm ngày 20–21/10/2026, giá tính bằng USD. Mã trong ngoặc vuông là mã cũ để đối chiếu (“v1 x.y” là số câu ở bảng hỏi trước). “Tham khảo” ghi cách Tern, TravelJoy và các phần mềm khác làm, kèm link nguồn; “không công bố” nghĩa là nguồn công khai không nói tới.

**Từ ngữ**
- Add-on: phần trả thêm, bật riêng ngoài gói.
- DPA: thoả thuận xử lý dữ liệu, phụ lục của hợp đồng đối tác.
- Sub-processor: bên thứ ba xử lý dữ liệu thay AA, phải ghi tên trong DPA.
- Issue: một phần việc lập trình, khoảng 1–3 ngày.
- Owner: chủ đại lý.
- Office hours: buổi hỏi đáp trực tuyến theo nhóm, theo lịch cố định.
- Chuyển tiếp/BCC: đại lý chuyển thư, hoặc thêm một địa chỉ BCC, để thư vào CRM mà CRM không phải đọc cả hộp thư.
- CASA: đợt kiểm định bảo mật hằng năm Google đòi khi app đọc hộp thư Gmail.
- Mở khẩn cấp (break-glass): quyền đặc biệt để AA mở dữ liệu một đại lý khi có sự cố an ninh hoặc lệnh pháp lý.
- Waiver: giấy cam kết tự chịu rủi ro khi đi trekking.

---

## 1. Giá và thu tiền

Giá net cho đại lý, cách AA thu tiền đại lý, ràng buộc giá bán và người nhập giá. Mô hình giá của CRM đã quyết định (xem cuối trang).

### 1.1 Giá net cho đại lý (cần xác nhận) [v1 1.2, Q1.2, H9]
**Bối cảnh:** Đã có câu trả lời tạm (lựa chọn a): chỉ cần xác nhận; các lựa chọn khác chỉ dùng khi muốn sửa. API tồn kho AA trả giá net cho CRM (spec §9 AA inventory API); báo giá ở module 6. CRM miễn phí cho đại lý lúc mở (đã quyết định), nên AA thu từ biên lợi nhuận tour AA.

**Tham khảo:**
- Tern, TravelJoy: không áp dụng, vì không bán tour của chính họ. ([Tern](https://tern.travel/pricing), [TravelJoy](https://traveljoy.com/pricing))
- Asian Trails (DMC bán B2B): bảng giá cho đại lý nằm ở kho Cloud Tariff chỉ dành cho đại lý, đặt chỗ qua cổng eConnect; không công bố biên giá. ([Cloud Tariff](https://www.asiantrails.travel/?p=1032235), [eConnect](https://www.asiantrails.travel/?p=1032376))

**Lựa chọn:**
- a) Dùng bảng giá net B2B đang có (biên 15%); đại lý tự đặt giá bán cho khách của họ. **← đề xuất (xác nhận)**
- b) Hoặc sửa: lập bảng giá net riêng cho đại lý dùng CRM.
- c) Hoặc sửa: giá net theo hạng đại lý (theo khối lượng bán).

**Lý do đề xuất:** Bảng giá đã có sẵn, không phải duy trì thêm bảng thứ hai.

### 1.2 Cách AA thu tiền đại lý khi đại lý bán tour AA (cần xác nhận) [v1 1.3, Q1.3]
**Bối cảnh:** Đã có câu trả lời tạm (lựa chọn a): chỉ cần xác nhận và điền điều khoản B2B hiện tại; các lựa chọn khác chỉ dùng khi muốn sửa. Đã quyết định AA xuất hoá đơn cho đại lý. Phần cần điền: trả trước hay công nợ, % cọc, tiền tệ hoá đơn, phí thẻ 3% có áp cho chuyển khoản không (spec module 6, 7; §11 gap 6: AUD/USD/VND/EUR). Tiền khách trả đại lý đi qua Stripe của đại lý (đã quyết định); tiền đại lý trả AA đi ngoài CRM.

**Tham khảo:**
- Tern, TravelJoy: không áp dụng, vì không bán tour của chính họ. ([Tern](https://tern.travel/pricing), [TravelJoy](https://traveljoy.com/pricing))
- Asian Trails: điều khoản thanh toán với đại lý không công bố. ([eConnect](https://www.asiantrails.travel/?p=1032376))

**Lựa chọn:**
- a) Dùng đúng điều khoản B2B AA đang áp cho đại lý hiện tại (công nợ, cọc, tiền tệ, phí thẻ như hiện nay). **← đề xuất (xác nhận)**
- b) Hoặc sửa: đại lý trả trước 100% trước ngày khởi hành, không công nợ.
- c) Hoặc sửa: cọc khi xác nhận, phần còn lại trước ngày khởi hành, theo điều khoản mới (ghi: % cọc, hạn trả, tiền tệ hoá đơn, phí thẻ có áp cho chuyển khoản không).

**Lý do đề xuất:** Không tạo thêm một quy trình thu tiền thứ hai cho cùng một loại khách B2B.

### 1.3 Báo giá thấp hơn giá “từ …” công khai của AA (cần xác nhận) [v1 1.4, Q1.4]
**Bối cảnh:** Đã có câu trả lời tạm (lựa chọn a): chỉ cần xác nhận; các lựa chọn khác chỉ dùng khi muốn sửa. Đại lý tự đặt giá bán (module 3). Hợp đồng đối tác có ở spec §10 Non-code track phase 1 (điều khoản không lôi kéo khách); spec không nói về ràng buộc giá.

**Tham khảo:**
- Tern, TravelJoy: không áp dụng, vì không bán tour của chính họ. ([Tern](https://tern.travel/pricing), [TravelJoy](https://traveljoy.com/pricing))
- Asian Trails: quy định giá bán lại không công bố. ([Cloud Tariff](https://www.asiantrails.travel/?p=1032235))

**Lựa chọn:**
- a) Chỉ ghi trong hợp đồng đối tác; CRM cảnh báo, không chặn. **← đề xuất (xác nhận)**
- b) Hoặc sửa: CRM chặn mọi báo giá thấp hơn giá công khai.
- c) Hoặc sửa: không ràng buộc.

**Lý do đề xuất:** Đại lý giữ quyền đặt giá, AA vẫn có căn cứ trong hợp đồng.

### 1.4 Người nhập giá net nhà cung cấp và bảng giá tour (cần xác nhận) [v1 1.5, Q1.5]
**Bối cảnh:** Đã có câu trả lời tạm (lựa chọn a): chỉ cần xác nhận và điền tên người phụ trách; các lựa chọn khác chỉ dùng khi muốn sửa. Báo giá tự động (module 3) cần giá thật trong AA-Booking (spec §9 AA inventory API). Trên Dev hiện dùng giá giả.

**Tham khảo:**
- Tern, TravelJoy: không áp dụng, vì không bán tour của chính họ. ([Tern](https://tern.travel/pricing), [TravelJoy](https://traveljoy.com/pricing))
- Asian Trails: kho Cloud Tariff chỉ dành cho đại lý, đăng sẵn bảng giá cả năm (bản mới: 11/2025–2026). ([Cloud Tariff](https://www.asiantrails.travel/?p=1047131))

**Lựa chọn:**
- a) Đội ops/sản phẩm hiện tại nhập, xong trước khi chọn 3–5 đại lý thử nghiệm (ghi tên người phụ trách). **← đề xuất (xác nhận)**
- b) Hoặc sửa: nhập dần từng tour khi đại lý hỏi tới.
- c) Hoặc sửa: nhập sau khi đã chọn đại lý thí điểm, chỉ các tour các đại lý đó bán.

**Lý do đề xuất:** Đại lý thật dùng báo giá tự động ngay từ ngày đầu, nên giá phải có trước.

---

## 2. Hỗ trợ đại lý

Ai của AA hỗ trợ đại lý mới, qua kênh nào, mất bao nhiêu giờ.

### 2.1 Hỗ trợ và hướng dẫn đại lý mới [v1 2.4, R43]
**Bối cảnh:** Spec §11 gap 5: “Onboarding module: import from Gmail / CSV, first-run setup, team invites”. F4: người dùng mới cài đặt xong dưới 5 phút. Spec không nói ai hỗ trợ, giờ hay kênh hỗ trợ. Thí điểm 3–5 đại lý (§10 Pilot). Bản trước đề xuất mỗi đại lý một người AA đồng hành, qua email và WhatsApp; bản này đổi sang mô hình ít người vì AA không có nhiều người cho việc này. Đại lý tự import dữ liệu khách, nhân viên AA không chạm file khách.

**Tham khảo:**
- Tern: bot Fin tự giải quyết hơn 85% hội thoại; khoá Tern & Learn; webinar sản phẩm hằng quý; gọi 1-1 khi việc gấp. ([blog](https://www.tern.travel/blog/the-future-of-human-support.html), [trợ giúp](https://help.tern.travel/en/))
- TravelJoy: bot T.J. trả lời trước rồi chuyển người; live chat chỉ ở gói Pro/Premium, trong giờ hành chính; workshop trực tuyến hằng tuần, có bản ghi. ([hỗ trợ](https://help.traveljoy.com/hc/en-us/articles/360016023172-How-to-reach-TravelJoy-support), [workshop](https://traveljoy.com/blog/post/traveljoy-training-workshops))
- HubSpot: người dùng miễn phí chỉ được hỗ trợ qua cộng đồng; email/chat từ gói Starter; có HubSpot Academy. ([hỗ trợ](https://help.hubspot.com))
- Pipedrive: chatbot và live chat 24/7 cho mọi gói; điện thoại chỉ ở gói Premium/Ultimate. ([liên hệ](https://support.pipedrive.com/en/contact-us))

**Lựa chọn:**
- a) Tự phục vụ trước, một người AA cho cả 3–5 đại lý thí điểm: danh sách việc lần đầu trong app (nối Gmail, mời nhân viên, tự import CSV); trang trợ giúp tiếng Anh kèm 15–20 video ngắn; office hours nhóm 30–45 phút, 2 tuần một lần, có ghi hình; một hộp thư hỗ trợ chung, trả lời trong 1 ngày làm việc (giờ VN), không WhatsApp 1-1; mỗi đại lý 1 cuộc gọi khởi động 45 phút và 1 lần hỏi thăm ở tuần thứ 2 (≈ 3–4 giờ/đại lý trong tháng đầu, sau đó ≈ 1 giờ/tuần); bot trợ giúp (≈ $1–3/tháng) bật khi đã gom khoảng 50 câu hỏi thật (ghi tên người phụ trách). **← đề xuất**
- b) Mỗi đại lý một người AA đồng hành; email và WhatsApp trong giờ hành chính VN.
- c) Chỉ trang trợ giúp, video và email; không có người phụ trách, không gọi khởi động.

**Lý do đề xuất:** Cần ít giờ người nhất mà đại lý thí điểm vẫn có người gọi được. Giống cách Tern và TravelJoy: tài liệu, buổi nhóm và bot trước, người thật khi cần. Bản ghi office hours dùng lại làm video trợ giúp.

---

## 3. Pháp lý và dữ liệu

Pháp nhân, thời điểm thuê luật sư và lời hứa quyền riêng tư với đại lý. Các điểm kỹ thuật về dữ liệu đã quyết định (xem cuối trang).

### 3.1 Pháp nhân ký hợp đồng với đại lý (cần xác nhận) [v1 3.1, Q2.1, H5]
**Bối cảnh:** Đã có câu trả lời tạm (lựa chọn a): chỉ cần xác nhận và điền tên pháp nhân; các lựa chọn khác chỉ dùng khi muốn sửa. Hợp đồng đối tác và DPA (spec §10 Non-code track phase 0–1). Cùng pháp nhân này đứng tên tài khoản nền tảng Stripe, tài khoản xác minh app với Google và Microsoft. Thời điểm thuê luật sư hỏi riêng ở 3.2.

**Tham khảo:**
- Tern, TravelJoy: không áp dụng (việc nội bộ của AA).
- Google: xác minh app cần tên miền đã xác minh, trang chủ và chính sách riêng tư cùng tên miền. ([Google](https://developers.google.com/identity/protocols/oauth2/production-readiness/sensitive-scope-verification))
- Microsoft: xác minh nhà phát hành cần tài khoản Microsoft AI Cloud Partner Program và tên miền đã xác minh. ([Microsoft](https://learn.microsoft.com/en-us/entra/identity-platform/publisher-verification-overview))

**Lựa chọn:**
- a) Pháp nhân AA đang dùng cho hợp đồng đối tác (ghi tên); dùng mẫu DPA đã soạn. **← đề xuất (xác nhận)**
- b) Hoặc sửa: dùng một pháp nhân khác cho sản phẩm CRM (ghi tên).

**Lý do đề xuất:** Dùng lại pháp nhân và mẫu đã có.

### 3.2 Thời điểm thuê luật sư (cần xác nhận) [v1 3.2, Q3.9]
**Bối cảnh:** Đã có câu trả lời tạm (lựa chọn a): chỉ cần xác nhận; các lựa chọn khác chỉ dùng khi muốn sửa. Luật sư xem luật dữ liệu VN, EU, Úc, hợp đồng đối tác, DPA và waiver. Spec §10 Non-code track đặt rà luật (Privacy Act Úc, GDPR, luật dữ liệu VN) và mẫu DPA ở phase 0, tức trước khi lưu dữ liệu khách thật. Lựa chọn a dời việc này tới các mốc rủi ro; đại lý thí điểm đầu tiên ở ngoài EU và VN (ví dụ Úc). Chưa có báo giá luật sư.

**Tham khảo:**
- Tern, TravelJoy: không áp dụng (việc nội bộ của AA).
- HubSpot: khuyên khách tự hỏi luật sư về hiệu lực chữ ký điện tử theo luật nước sở tại. ([HubSpot](https://knowledge.hubspot.com/quotes/use-e-signatures-with-quotes))

**Lựa chọn:**
- a) Gửi bản tóm tắt cho luật sư khi chạm một trong ba mốc: đại lý VN/EU muốn dùng dữ liệu thật; có đại lý thứ 6; 60 ngày sau khách thật đầu tiên. **← đề xuất (xác nhận)**
- b) Hoặc sửa: thuê ngay bây giờ.
- c) Hoặc sửa: thuê trước khi mở cho 3–5 đại lý thử nghiệm (đúng thứ tự spec).

**Lý do đề xuất:** Chi phí luật sư đi cùng rủi ro thật, không trả khi mới có dữ liệu giả. Nếu muốn bám đúng thứ tự spec thì chọn c.

### 3.3 Lời hứa quyền riêng tư với đại lý, và câu chữ spec đi kèm [v1 3.3, 3.4, 3.6; Q2.2, H3]
**Bối cảnh:** Spec §1 coi “AA không thấy khách là ai” là một trong ba điểm khác biệt của sản phẩm. F1: “No access outside the agency, AA included”. §8: AA chỉ nhận dữ liệu ops của chuyến đã chốt (module 8) và số liệu gộp k ≥ 10 (module 17), “never contact details or non-AA bookings”. §2: dữ liệu khách thuộc về đại lý.

Điểm riêng của AA: AA vừa cung cấp phần mềm vừa bán tour, nên đại lý sẽ hỏi “AA có thấy khách của tôi không”. Chính sách quyền riêng tư chung không trả lời câu này.

Thiết kế có 3 lớp: AA quản lý tài khoản mà không xem hồ sơ khách; hỗ trợ chỉ khi chủ đại lý cấp quyền (đã quyết định: mặc định 24 giờ, chủ chọn 1–7 ngày, chỉ đọc, ẩn danh tính khách, chặn export); mở khẩn cấp (đã quyết định: chỉ khi sự cố an ninh hoặc lệnh pháp lý, đăng nhập hai bước, tối đa 1 giờ, mỗi lần một đại lý, tự hiện trong nhật ký, email chủ đại lý trong 24 giờ). Phần kỹ thuật đã nằm trong thiết kế, không tốn thêm chi phí hạ tầng. Câu này chỉ hỏi câu chữ và chỗ đặt lời hứa; hai điều khoản trên giữ nguyên ở mọi lựa chọn.

Câu hứa đề xuất (đặt trong DPA và trang dữ liệu công khai, không làm khẩu hiệu): “AA quản lý tài khoản đại lý mà không xem hồ sơ khách. AA chỉ nhận thông tin khách của chuyến đã chốt có dịch vụ AA, để vận hành tour, và xoá 90 ngày sau chuyến. AA chỉ xem số liệu gộp, không xem từng khách. Nhân viên hỗ trợ của AA chỉ xem được khi chủ đại lý tự cấp quyền có thời hạn, chỉ đọc, ẩn danh tính khách. Khẩn cấp về an ninh hoặc pháp lý thì AA có thể mở dữ liệu của một đại lý, phải đăng nhập hai bước, việc đó tự hiện trong nhật ký của đại lý và chủ đại lý nhận email trong 24 giờ.”

Câu chữ spec phải sửa cho khớp (lựa chọn a):
- F1, cột quyền: “No access outside the agency, AA included” → “No access outside the agency, AA included, except confirmed-trip ops data (module 8), owner-granted read-only support, and audited emergency access”.
- F1, cột nội dung: “encrypted with the agency's own key” → “encrypted with a per-agency data key; agency-held key available on request”.
- §8 Agency controls: “agency-held keys” → “per-agency keys (agency-held key on request)”.

**Tham khảo:**
- Tern: privacy policy (12/2025) chỉ hứa “reasonable safeguards”, không nói nhân viên Tern có xem dữ liệu không. ([privacy](https://www.tern.travel/privacy), [bảo mật](https://help.tern.travel/en/articles/8126635-data-privacy-and-security-in-tern))
- TravelJoy: privacy policy (29/05/2026) chỉ hứa “appropriate … security measures”, không nói về nhân viên hỗ trợ. ([privacy](https://traveljoy.com/privacy))
- HubSpot: không có lời hứa riêng; DPA ghi thẳng “a subset of our employees have access to the products and to customer data via controlled interfaces”, kèm nút cho hỗ trợ vào 24 giờ. ([DPA](https://legal.hubspot.com/dpa), [quyền hỗ trợ](https://knowledge.hubspot.com/account-security/limit-logins-to-trusted-ip-addresses))
- Zoho CRM: khách tự bật quyền hỗ trợ, có hạn, chặn export, ghi nhật ký. ([Zoho](https://help.zoho.com/portal/en/community/topic/support-access-for-zoho-crm))
- Zendesk: có quyền vào tài khoản khách không báo trước khi khẩn cấp. ([Zendesk](https://support.zendesk.com/hc/en-us/articles/4408824477082))
- Tóm lại: thị trường ghi điều khoản trong DPA và trang bảo mật, không làm lời hứa marketing.

**Lựa chọn:**
- a) Có lời hứa riêng như câu đề xuất, đặt trong DPA và trang dữ liệu công khai; sửa câu chữ F1 và §8 của spec như trên. **← đề xuất**
- b) Không có lời hứa riêng; chỉ dùng chính sách quyền riêng tư chung (như Tern, TravelJoy, HubSpot); vẫn sửa câu chữ spec cho đúng kỹ thuật.
- c) Lời hứa ngắn hơn, chỉ ghi trong DPA, không đặt trên trang dữ liệu công khai; điều khoản mở khẩn cấp giữ như đã quyết định; vẫn sửa câu chữ F1 và §8 của spec như trên.

**Lý do đề xuất:** Trả lời đúng câu đại lý sẽ hỏi một nhà cung cấp cũng bán tour, và nói đúng sự thật về hai ngoại lệ có trong spec (module 8, module 17) và trường hợp khẩn cấp. Thị trường để điều khoản trong DPA, nên câu hứa cũng nằm ở đó. Lựa chọn c ít chữ hơn, nhưng đại lý chỉ đọc trang dữ liệu công khai sẽ không thấy câu trả lời cho câu hỏi đó.

---

## 4. Email của đại lý

Phạm vi đồng bộ email so với chữ của spec module 5. Các dịch vụ bên ngoài khác đã quyết định (xem cuối trang).

### 4.1 Gửi và nhận email qua Gmail/Outlook của đại lý [v1 4.7, Q3.6]
**Bối cảnh:** Spec module 5: “Two-way Gmail / Outlook sync … Agency stops using Gmail for client work”; §9 Gmail/Outlook: “OAuth scopes, threading, send-as”. Outlook làm cùng lúc với Gmail (đã quyết định, đúng spec).

Chỉ xin quyền gửi thư (gmail.send) thì Google xác minh miễn phí. Đọc hộp thư là quyền loại restricted, phải qua kiểm định bảo mật CASA hằng năm (≈ $675–5.400/năm, tìm hiểu 20/10/2026; Google không công bố giá).

Lựa chọn a lệch chữ spec module 5: thư đến vào CRM qua địa chỉ chuyển tiếp/BCC chứ không kéo cả hộp thư về.

**Tham khảo:**
- TravelJoy: chỉ gửi đi bằng Gmail của đại lý, không đồng bộ hộp thư. ([Gmail](https://help.traveljoy.com/hc/en-us/articles/360028239552-Connect-your-Google-Mail-account-to-TravelJoy))
- Tern: đồng bộ toàn bộ thư Google/Microsoft. ([email](https://help.tern.travel/en/articles/9015404-an-introduction-to-email-in-tern))
- Pipedrive: chuyển tiếp Smart BCC ở mọi gói; đồng bộ email từ gói Growth. ([Smart BCC](https://support.pipedrive.com/en/article/smart-email-bcc), [email sync](https://support.pipedrive.com/article/email-sync))
- HubSpot: mặc định chỉ ghi thư gửi từ HubSpot, thư BCC và thư trả lời trong luồng đã ghi; muốn ghi mọi thư phải bật quy tắc ghi thư theo liên hệ. ([kết nối hộp thư](https://knowledge.hubspot.com/connected-email/connect-your-inbox-to-hubspot), [thư trả lời](https://knowledge.hubspot.com/email/log-email-replies-in-the-crm))
- Google: phân loại quyền Gmail. ([scopes](https://developers.google.com/workspace/gmail/api/auth/scopes))

**Lựa chọn:**
- a) Bản đầu: gửi đi từ Gmail/Outlook của đại lý; thư đến vào CRM qua địa chỉ chuyển tiếp/BCC; $0. Đồng bộ hai chiều chỉ làm khi đại lý đòi. Sửa câu module 5 của spec cho khớp. **← đề xuất**
- b) Đồng bộ hai chiều ngay như spec; AA trả kiểm định CASA hằng năm.

**Lý do đề xuất:** Đơn giản nhất và $0, giống cách mặc định của HubSpot và gói thấp nhất của Pipedrive; TravelJoy bán được chỉ với gửi đi. Đồng bộ hai chiều vẫn làm được sau, khi có đại lý đòi.

---

## 5. Bảo hiểm và waiver

Hãng bảo hiểm của AA và hai việc spec cần hãng xác nhận.

### 5.1 Hãng bảo hiểm duyệt waiver và chữ ký điện tử [v1 5.1, 4.1; Q4.1, H6, R13]
**Bối cảnh:** Spec module 12: ký điện tử điều khoản và waiver trekking, thành công khi “100% signed before departure; accepted by insurer”. §4: muốn qua Booked phải có “waiver signed”. §10 Non-code track phase 2: “Trekking waiver reviewed by AA's insurer”. §5 Stage 3 hỏi khách mục “travel insurance”. Spec không nói về bán bảo hiểm trong app, hoa hồng hay giấy từ chối bảo hiểm.

Đã quyết định: AA tự làm chữ ký điện tử đơn giản (mã một lần qua email, gõ tên, bấm đồng ý, PDF niêm phong, nhật ký ký), ≈ $0–1/tháng; nếu hãng bảo hiểm đòi nhà cung cấp ký có tên tuổi thì đổi sang BoldSign (từ $30/tháng gồm 40 lượt ký, thêm $0,75/lượt, gói Enterprise API, [BoldSign](https://boldsign.com/pricing); khoảng 2–3 issue). Mẫu waiver song ngữ Anh–Việt do AA soạn từ điều khoản hiện tại.

Bản đầu: mục “travel insurance” ở Stage 3 thêm lựa chọn “tôi không mua bảo hiểm”, nằm trong cùng văn bản ký với waiver. Bán bảo hiểm trong app để sau 23 module; hoa hồng đã quyết định (xem cuối trang).

Cần điền dù chọn a hay b: tên hãng bảo hiểm (hãng AA đang dùng hoặc hãng khác) và người liên hệ.

**Tham khảo:**
- Tern: báo giá bảo hiểm trong app với 4 hãng (Arch RoamRight, Faye, Chubb, Trawick); khách từ chối thì nhận email kèm biên nhận PDF; tự làm khối ký trong form. ([bảo hiểm](https://tern.travel/insurance), [từ chối bảo hiểm](https://help.tern.travel/en/articles/8857059-collecting-travel-insurance-authorization-opt-out), [ký trong form](https://help.tern.travel/en/articles/9670279-can-i-add-an-e-signature-to-my-forms))
- TravelJoy: bán Faye (hoa hồng 24%) và Arch RoamRight (hợp tác công bố 30/07/2026); form có chữ ký, nhật ký gửi/mở/ký kèm IP. ([báo giá](https://traveljoy.com/blog/post/how-to-search-quote-and-book-on-traveljoy), [Arch RoamRight](https://insurance.archgroup.com/arch-roamright-partners-with-traveljoy-to-simplify-travel-insurance-sales-for-travel-advisors/), [ký](https://traveljoy.com/blog/post/traveljoy-travel-agency-software-updates-feb-2025))
- Pipedrive: tự làm ký số cơ bản, người ký nhận mã một lần qua email. ([Smart Docs](https://support.pipedrive.com/en/article/sales-documents-esignatures-beta))
- HubSpot: ký báo giá bằng Dropbox Sign nhúng sẵn, khuyên khách tự hỏi luật sư về hiệu lực. ([HubSpot](https://knowledge.hubspot.com/quotes/use-e-signatures-with-quotes))

**Lựa chọn:**
- a) Hỏi hãng bảo hiểm hai việc: (1) duyệt mẫu waiver trekking; (2) có chấp nhận chữ ký điện tử AA tự làm không. Bản đầu chỉ có lựa chọn “tôi không mua bảo hiểm” ký chung với waiver (ghi tên hãng và người liên hệ). **← đề xuất**
- b) Như a, và hỏi luôn sản phẩm bảo hiểm du lịch cho khách đại lý kèm hoa hồng, để làm báo giá bảo hiểm trong app sớm (ghi tên hãng và người liên hệ).

**Lý do đề xuất:** Đúng hai việc spec đòi (hãng duyệt waiver, hãng chấp nhận cách ký). Câu trả lời về chữ ký quyết luôn có cần nhà cung cấp ký bên ngoài hay không. Bán bảo hiểm trong app không có trong spec nên để sau.

---

## 6. Vận hành và người phụ trách

Người của AA phụ trách lịch khởi hành, xác nhận tour và nhận báo động.

### 6.1 Xác nhận tour và người phụ trách lịch khởi hành (cần xác nhận) [v1 6.2, Q5.4, H8]
**Bối cảnh:** Đã có câu trả lời tạm (lựa chọn a): chỉ cần xác nhận và điền tên người phụ trách; các lựa chọn khác chỉ dùng khi muốn sửa. Giữ chỗ và xác nhận qua API tồn kho AA (spec §9; module 3, 8). Còn thiếu tên người ở đội ops nhập lịch khởi hành và xác nhận tour theo yêu cầu.

**Tham khảo:**
- Tern, TravelJoy: không áp dụng, vì không bán tour của chính họ. ([Tern](https://tern.travel/pricing), [TravelJoy](https://traveljoy.com/pricing))
- Asian Trails: cổng eConnect cho đại lý đặt với giá và chỗ trống theo thời gian thực. ([eConnect](https://www.asiantrails.travel/?p=1032376))

**Lựa chọn:**
- a) Tour có lịch cố định tự xác nhận; tour khác “theo yêu cầu”, AA ops xác nhận trong 1 ngày làm việc; ghi tên người phụ trách. **← đề xuất (xác nhận)**
- b) Hoặc sửa: mọi tour đều do AA ops xác nhận tay.

**Lý do đề xuất:** Đại lý có câu trả lời ngay cho tour cố định, ops chỉ xử lý phần cần người.

### 6.2 Người thứ hai nhận báo động khi AA mở dữ liệu khẩn cấp (cần xác nhận) [v1 3.4, V22-Q5]
**Bối cảnh:** Đã có câu trả lời tạm (lựa chọn a): chỉ cần xác nhận và điền tên người. Điều khoản mở khẩn cấp đã quyết định (chỉ khi sự cố an ninh hoặc lệnh pháp lý; đăng nhập hai bước; tối đa 1 giờ; mỗi lần một đại lý; tự hiện trong nhật ký đại lý; email chủ đại lý trong 24 giờ). Mỗi lần quyền này được dùng, hệ thống tự gửi báo động. Đội kỹ thuật chỉ có một người, nên cần một người thứ hai không phải kỹ sư nhận báo động. Người này chỉ được báo, không phải duyệt, và xem lại lý do trong nhật ký sau mỗi lần. Việc có người thứ hai nhận báo động cũng đã quyết định; câu này chỉ hỏi tên. Cần có tên trước khi mở cho đại lý thật.

**Tham khảo:**
- AWS Well-Architected (SEC10-BP05): mọi lần dùng role khẩn cấp phải ghi log và báo động; báo động phải tới một nhóm rộng và được xử lý ngay. ([AWS](https://docs.aws.amazon.com/wellarchitected/latest/framework/sec_incident_response_pre_provision_access.html))
- Tern, TravelJoy: không công bố. ([Tern privacy](https://www.tern.travel/privacy), [TravelJoy privacy](https://traveljoy.com/privacy))

**Lựa chọn:**
- a) Một quản lý AA không phải kỹ sư nhận email và tin nhắn mỗi lần quyền khẩn cấp được dùng; chỉ được báo, không duyệt (ghi tên; có thể ghi thêm một người dự phòng khi người này nghỉ). **← đề xuất (xác nhận)**

**Lý do đề xuất:** AWS khuyên báo động tới nhiều hơn một người. Với đội một kỹ sư, người nhận thứ hai là cách kiểm chéo duy nhất, mà gần như không tốn giờ. Người dự phòng là tuỳ chọn, để có người thấy báo động khi người chính nghỉ.

---

## Đã quyết định (không cần trả lời)

Mã trong ngoặc vuông là số câu ở bảng hỏi trước; số câu nhắc trong nội dung là số ở bản 2.

**Giá và mô hình kinh doanh**
- **[1.1] Mô hình giá CRM.** Lúc mở, mọi tính năng miễn phí cho đại lý (đúng spec §1). Về sau: phần lõi CRM miễn phí mãi; gói cao hoặc add-on trả phí cho AI soạn nháp vượt mức dùng hợp lý, chiến dịch email, đặt tour đoàn và báo cáo đầy đủ. Chuyển sang mô hình có gói trả phí khi gặp MỘT trong các mốc: (1) chi phí CRM hằng tháng (AWS + AI, theo báo cáo chi phí hằng tháng) vượt $150, khoảng gấp đôi mức ước tính ≈ $71/tháng cho 10 đại lý (thiết kế v2.2 §5.2), hoặc có 20 đại lý đang dùng; (2) một tính năng gói cao (đặt tour đoàn hoặc chiến dịch email) làm xong và có đại lý xin dùng; (3) có đại lý dùng CRM đều đặn nhưng 2 quý liền không đặt tour AA nào (AA đếm qua booking của chính AA, không xem doanh số đại lý). Để không thất hứa: hợp đồng đối tác ghi ngay từ đầu “Phần lõi CRM miễn phí. AA có thể thêm gói trả phí cho tính năng mới, báo trước 60 ngày”; có mức dùng AI hợp lý (fair-use) từ ngày đầu; đại lý thí điểm giữ phần lõi miễn phí vĩnh viễn; không bao giờ thu theo % doanh số.

**Sản phẩm cho đại lý**
- **[2.1] Đặt tour theo đoàn:** làm sau 23 module, dùng lịch khởi hành và số chỗ giữ sẵn của AA-Booking; thuộc gói cao/add-on khi có gói trả phí.
- **[2.2] Chiến dịch email:** chỉ gửi khách đã đồng ý nhận marketing, có huỷ đăng ký, gửi bằng tên đại lý, có nội dung AA làm sẵn để đại lý chọn. AA không bao giờ gửi tin cho khách của đại lý (spec §2).
- **[2.3] Mục “Trước khi đi”:** AA viết các gói chuẩn bị; visa chỉ đưa link cổng chính thức, không viết lời khuyên visa; bảo hiểm chỉ nhắc và trỏ sang giấy từ chối hoặc hãng ở 5.1; đại lý sửa được trước khi gửi.
- **[2.5] Báo đổi giờ bay:** bước đầu $0, nhắc 48 giờ trước giờ bay “xác nhận chuyến bay đến” kèm link xem trạng thái; chỉ mua API trả phí khi ops báo có lỡ đón thật, và nêu giá để duyệt trước khi bật.
- **[2.6] Tên miền:** một tên miền trung tính cho sản phẩm; đại lý nào muốn thì tự cài tên miền riêng; email gửi từ hộp thư của đại lý.
- **[2.7] Zalo:** bản đầu không có; xem lại khi có đại lý VN dùng dữ liệu thật.

**Pháp lý và dữ liệu**
- **[3.4] Mở dữ liệu khẩn cấp:** chỉ khi sự cố an ninh hoặc lệnh pháp lý; đăng nhập hai bước; tối đa 1 giờ; mỗi lần một đại lý; tự hiện ngay trong nhật ký đại lý; email báo chủ đại lý trong 24 giờ. Người thứ hai nhận báo động hỏi ở 6.2; câu chữ với đại lý ở 3.3.
- **[3.5] Quyền hỗ trợ của AA:** chỉ khi chủ đại lý tự bật; mặc định 24 giờ, chủ đại lý chọn được 1–7 ngày; chỉ đọc; ẩn danh tính khách; chặn export; mỗi lần một nhân viên; mọi lần xem ghi nhật ký; thu hồi bất cứ lúc nào. DPA ghi nguyên tắc (chủ đại lý cấp, có hạn, ghi nhật ký, thu hồi được); con số 24 giờ ghi ở trang trợ giúp.
- **[3.6] Khoá mã hoá:** mỗi đại lý một khoá dữ liệu riêng; khoá do đại lý tự giữ chỉ làm khi có đại lý hỏi, thiết kế đã để sẵn chỗ nên không phải mã hoá lại dữ liệu. Câu chữ F1 và §8 sửa theo 3.3.
- **[3.7] Xoá dữ liệu:** lời hứa “Xoá ngay trong ứng dụng. Không đọc lại được ở bất kỳ đâu, kể cả bản sao lưu, trong vòng tối đa 30 ngày”, với điều kiện bản sao lưu dữ liệu CRM giữ tối đa 30 ngày. Nếu không giữ được điều kiện này thì hứa 90 ngày. Ngoại lệ ghi rõ: nhật ký truy cập (không chứa thông tin khách) và chứng từ kế toán luật bắt buộc giữ.
- **[3.8] Nhật ký “ai đã xem gì”:** đại lý xem được 12 tháng trong app, không sửa được; sau đó lưu thêm 6 năm, vẫn chống sửa nhưng rút ngắn được nếu luật sư khuyên khác (3.2); đại lý tải được bản sao; chưa gửi liên tục sang hệ thống khác của đại lý.
- **[3.9]** Nhật ký đại lý hiện dòng “AA ops đã xem thông tin chuyến X ngày Y”.
- **[3.10] Thông tin gửi khách sạn, xe:** chỉ họ tên, số người, yêu cầu ăn uống/đi lại; số hộ chiếu chỉ khi nhà cung cấp bắt buộc; mỗi lần xuất danh sách đều ghi nhật ký.
- **[3.11] Bên xử lý dữ liệu (sub-processor):** DPA và một trang danh sách công khai ghi tên công ty và mục đích, không ghi từng tài khoản máy chủ: “Amazon Web Services, Inc.: lưu trữ (us-west-1) và AI soạn nháp (Amazon Bedrock). Văn bản đã lọc thông tin cá nhân trước khi gửi. Không lưu, không dùng để huấn luyện.” Báo trước 30 ngày khi danh sách thay đổi.
- **[3.12] Số liệu tổng hợp AA được xem:** mỗi nhóm có ít nhất 10 khách (spec module 17) và từ ít nhất 3 đại lý; áp mặc định cho mọi đại lý, ghi trong hợp đồng và trang dữ liệu; đại lý muốn rút thì gửi yêu cầu. Xem lại ngưỡng khi có trên khoảng 50 đại lý.
- **[3.13] Đăng nhập hai bước:** bắt buộc cho chủ đại lý và nhân viên bán hàng (passkey trên điện thoại hoặc app xác thực).
- **[3.14] Chứng chỉ bảo mật:** chưa làm SOC 2/ISO 27001. Trang dữ liệu công khai (spec §10 phase 4) gồm: lời hứa ở 3.3, danh sách sub-processor, thời hạn xoá, thời gian giữ nhật ký, và câu “hạ tầng AWS có ISO 27001 và SOC 2” kèm link báo cáo của AWS, ghi rõ đó là chứng chỉ của AWS. Hỏi lại khi phỏng vấn đại lý thí điểm hoặc khi hãng bảo hiểm đòi.

**Dịch vụ bên ngoài**
- **[4.1] Ký điện tử:** AA tự làm chữ ký đơn giản (mã một lần qua email, gõ tên, bấm đồng ý, PDF niêm phong, nhật ký ký), ≈ $0–1/tháng. Nếu hãng bảo hiểm đòi nhà cung cấp ký có tên tuổi thì đổi sang BoldSign (từ $30/tháng, gói Enterprise API, [BoldSign](https://boldsign.com/pricing)). Câu hỏi cho hãng nằm ở 5.1.
- **[4.2, 4.4] WhatsApp và SMS:** theo spec, qua tài khoản Twilio của chính đại lý, dùng chung cho WhatsApp và SMS; đại lý trả phí Meta và Twilio, tự đăng ký số (người phụ trách ở 2.1 giúp); AA $0; không dùng 360dialog. Trước khi làm module 9, xác nhận với Twilio điều kiện cho phần mềm dùng tài khoản Twilio của khách ([Twilio self sign-up](https://www.twilio.com/docs/whatsapp/self-sign-up), [Twilio Tech Provider](https://www.twilio.com/docs/whatsapp/isv/tech-provider-program)). Nếu Twilio bắt buộc mô hình ISV: AA làm Meta Tech Provider, mỗi đại lý một subaccount Twilio dưới tài khoản AA, phí chuyển lại cho đại lý.
- **[4.3] Kênh nhắn tin lúc mở:** WhatsApp và SMS (module 9) có trong 23 module; Messenger, Instagram làm sau 23 module.
- **[4.5] Thanh toán thẻ:** Stripe Connect Standard, tiền vào thẳng tài khoản Stripe của đại lý; không lưu thẻ để uỷ quyền; AA $0; tài khoản nền tảng đứng tên pháp nhân ở 3.1, mở khi có đại lý thật; Dev dùng test mode.
- **[4.6] Cổng thanh toán VN:** chưa gấp; đại lý VN ghi tay khoản đã thu; xin báo giá cổng nội địa khi có đại lý VN dùng dữ liệu thật.
- **[4.8] Outlook:** làm cùng lúc với Gmail trong module 5, đúng spec; xác minh nhà phát hành Microsoft làm cùng đợt với Google ([6.1] bên dưới).
- **[4.9] Tường lửa web:** bật khi có đại lý thật; là chi phí nền tảng chung AA trả (≈ $7,5–10/tháng cho mọi đại lý); khi có gói trả phí thì nằm trong giá gốc của mọi gói, không thành add-on.

**Bảo hiểm và waiver**
- **[5.2] Hoa hồng bảo hiểm du lịch:** đại lý hưởng toàn bộ hoa hồng bảo hiểm du lịch; áp dụng khi làm bán bảo hiểm trong app (sau 23 module).
- **[5.3] Mẫu điều khoản và waiver:** AA soạn song ngữ Anh–Việt từ điều khoản hiện tại; đội kinh doanh AA rà lại; hãng bảo hiểm duyệt (5.1).

**Vận hành và thử nghiệm**
- **[6.1] Thủ tục với Google, Microsoft (và Meta nếu Twilio yêu cầu):** chỉ bắt đầu khi app CRM đủ 23 module trên Dev; nộp ngay ngày đó, song song với việc chọn và phỏng vấn đại lý. Google và Microsoft mỗi bên khoảng 1 tuần. Việc chuẩn bị không tốn tiền: tên pháp nhân (3.1), tên miền có trang chủ và chính sách riêng tư, kịch bản video demo.
- **[6.3] Khi chủ đại lý nghỉ hoặc mất tài khoản:** AA chỉ thăng một người đã là thành viên của đại lý lên chủ, sau 14 ngày chờ, có email báo chủ cũ và ghi nhật ký; ghi vào hợp đồng đối tác.

**Từ trước**
- **H1:** làm đủ 23 module của spec trước; đại lý thật chỉ dùng sau đó.
- **H4 [Q5.1]:** trên Dev chỉ dùng đại lý giả, dữ liệu giả; mọi dịch vụ trả phí dùng bản test hoặc miễn phí. Khi đủ 23 module (dự kiến giữa 12/2026 tới giữa 01/2027) sẽ chọn 3–5 đại lý thân quen ngoài EU và VN (ví dụ Úc), mỗi đại lý 30 phút phỏng vấn trước khi mở (spec §10 Pilot); câu chọn đại lý sẽ hỏi lúc đó.
- Các tính năng kỹ thuật từ so sánh Tern/TravelJoy và đợt ý tưởng 21/10 đưa thẳng vào thiết kế.
