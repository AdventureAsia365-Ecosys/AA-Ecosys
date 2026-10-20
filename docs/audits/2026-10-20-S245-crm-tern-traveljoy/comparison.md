# So sánh Tern, TravelJoy với spec của chị Thư và thiết kế CRM cho đại lý (PR-19)

Ngày 20/10/2026. Tác nhân: Claude Code. Tài liệu chỉ đọc và viết, không đổi repo, không gọi dịch vụ trả phí.

**Đầu vào đã đọc:**
- Hai bản phân tích công khai: `.tmp-session/crm-teardown/tern.md` và `.tmp-session/crm-teardown/traveljoy.md`.
- Spec của chị Thư: `docs/research/partner-crm-spec.md`.
- Thiết kế CRM, theo thứ tự phiên bản:
  - v1: `docs/audits/2026-10-20-S245-tenant-crm/README.md` (đã merge);
  - v2: `docs/audits/2026-10-20-S245-tenant-crm/v2/crm-design-v2.md` (nhánh `docs/s245-crm-r3-wm-plan`);
  - v2.1: `docs/audits/2026-10-20-S245-tenant-crm/v2.1/crm-design-v2.1-tech.md` và `thu-questions.md` (cùng nhánh);
  - **v2.2, bản mới nhất** (bản nháp, chưa vào repo): `.tmp-session/s245-r2/r4/crm-v2.2-simplified.md`, kèm bản khảo
    sát thị trường `.tmp-session/s245-r2/r4/market-travel-crm.md`.

**Cách đọc:**
- "Thiết kế hiện tại" là v2.2. Bản này giữ phần chức năng của v2/v2.1 và chỉ đổi phần kỹ thuật.
- Ký hiệu: **Có** / **Một phần** / **Chưa có**. Ở cột đối thủ, "Chưa có" nghĩa là **không thấy trong tài liệu công
  khai**, không có nghĩa chắc chắn họ không có.
- Ô của đối thủ có link nguồn. Ô của spec ghi số mục trong spec; ô của thiết kế ghi số mục trong v2 hoặc v2.2.

---

## 0. Tóm tắt

1. **Phần lõi của spec đã ngang hai đối thủ:** form nhận yêu cầu, pipeline, proposal có phương án cho khách chọn, hoá
   đơn, hoa hồng, AI soạn nháp có người duyệt, vai trò trong đại lý. Đây là mức tối thiểu để đại lý chịu dùng.
2. **Chỗ mình hơn hẳn (cả hai đối thủ đều không có):**
   - hàng của AA chạy sống trong CRM: giá net, chỗ trống, giữ chỗ và xác nhận;
   - tách riêng tư theo kiến trúc: AA không xem được danh tính khách;
   - luồng gửi thông tin khách cho AA ops rồi tự xoá sau 90 ngày;
   - WhatsApp;
   - nhiều tiền tệ, song ngữ Anh–Việt;
   - xuất toàn bộ dữ liệu và xoá có kiểm chứng;
   - nội dung marketing AA làm sẵn cho đại lý, có nút dẫn về form của đại lý.
3. **Chỗ cả hai đối thủ có mà mình còn thiếu:**
   - nhắc ngày đặc biệt (sinh nhật, hộ chiếu sắp hết hạn);
   - đặt tour theo đoàn;
   - AI đọc tài liệu của nhà cung cấp để tự điền lịch trình, hoá đơn, hộ chiếu;
   - bảo hiểm du lịch ngay trong app;
   - đồng bộ lịch Google/Outlook;
   - gắn tag để tự chạy quy trình;
   - gộp khách trùng;
   - app trên điện thoại cho khách.
4. **Chi phí:** đại lý đang trả Tern $35–49 mỗi người dùng một tháng, trả TravelJoy $19–99 một tháng cộng phí thẻ
   3,5–5%. Theo ước tính của v2.2, AA tốn khoảng **$4–7 mỗi đại lý một tháng**. Còn rất nhiều khoảng trống để giữ "miễn
   phí cho đối tác".
5. **Đề xuất (§5):** thêm 10 việc nhỏ, rẻ, hợp với ý "dễ vận hành" vào thiết kế, và đưa 6 việc lớn hơn cho chị Thư
   quyết. Có ba việc nên **không** làm: đồng bộ Gmail hai chiều, app điện thoại riêng, AI ghi âm cuộc gọi.

---

## 1. Ma trận tính năng

### 1.1 Khách hàng và nhận yêu cầu

| Module | Tern | TravelJoy | Spec chị Thư | Thiết kế hiện tại |
|---|---|---|---|---|
| Hồ sơ khách: sở thích, hộ chiếu, ngày sinh | **Có**: 39 trường, nhiều hộ chiếu mỗi khách, thẻ thành viên hãng (loyalty), KTN ([nguồn](https://help.tern.travel/en/articles/8719371-what-fields-are-supported-in-the-core-import)) | **Có**: sở thích, loyalty, chuyến cũ; mỗi khách chỉ **một** ảnh hộ chiếu ([nguồn](https://help.traveljoy.com/hc/en-us/articles/360047051511-Collect-and-store-client-passport-photos)) | **Có**: Stage 1–3, F1 lưu danh tính, F2 lưu hồ sơ ẩn danh (§5, §7) | **Một phần**: đủ như spec, nhưng chưa có loyalty và chỉ một hộ chiếu mỗi khách (v1 §8.2) |
| Quan hệ gia đình, người đi cùng | **Có**: 11 loại quan hệ, tự tạo chiều ngược lại ([nguồn](https://help.tern.travel/en/articles/9534524-how-to-import-relationships-in-tern)) | **Một phần**: thêm người đi cùng, mỗi người phải tự điền form và có email riêng ([nguồn](https://help.traveljoy.com/hc/en-us/articles/360016308471-Can-the-client-fill-out-a-form-multiple-times-to-cover-additional-travelers)) | **Một phần**: chỉ có vai trò "trưởng đoàn / đi cùng" trong một trip (§7) | **Một phần**: như spec |
| Form nhận yêu cầu tự tạo khách và trip | **Có**: nhúng vào web, khử trùng theo email + tên, một lần gửi khai được nhiều người ([nguồn](https://help.tern.travel/en/articles/8594104-managing-forms-in-tern)) | **Có**: nhúng vào web, có trang hỏi công khai; gửi trùng sẽ ra trip trùng ([nguồn](https://help.traveljoy.com/hc/en-us/articles/360016308691-Embed-a-client-inquiry-form-on-your-website)) | **Có**: module 1, dưới 2 phút, bắt buộc hỏi ngân sách theo khoảng | **Có**: form trên trang khách và widget nhúng, khử trùng khi nhận (v2 §5, §6) |
| Gộp khách trùng, nhập dữ liệu cũ | **Có**: trang tìm trùng và gộp; nhập theo 4 đợt (khách, quan hệ, chuyến cũ, ghi chú) ([nguồn](https://help.tern.travel/en/articles/14732085-how-to-find-and-merge-duplicate-contacts), [nguồn](https://help.tern.travel/en/articles/16787209-moving-to-tern-from-another-platform)) | **Một phần**: nhập danh sách khách, gộp trip trùng ([nguồn](https://help.traveljoy.com/hc/en-us/articles/360016022032-Import-your-client-list)) | **Một phần**: §11.5 còn để mở (nhập từ Gmail/CSV) | **Một phần**: nhập CSV và mbox; khử trùng lúc nhận nhưng chưa có màn gộp (v2 §5) |
| Đặt lịch gọi, đồng bộ lịch | **Có**: chọn giờ hẹn ngay trong form, đồng bộ Google/Microsoft ([nguồn](https://tern.travel/updates/a-new-era-of-crm-for-travel-advisors)) | **Có**: đồng bộ Google Calendar và Outlook ([nguồn](https://traveljoy.com/blog/post/traveljoy-a-comprehensive-crm-for-travel-agents)) | **Chưa có** | **Chưa có** |
| Gắn nguồn lead, nội dung marketing của đại lý | **Một phần**: dùng tag của trip để ghi nguồn; không gửi email hàng loạt ([nguồn](https://www.tern.travel/updates/automated-trip-statuses-new-reports-and-your-agency-back-office-home.html), [nguồn](https://help.tern.travel/en/articles/9528236-can-i-send-emails-to-multiple-recipients-at-once-like-a-marketing-email-campaign)) | **Một phần**: tab Marketing có trang hỏi công khai và chiến dịch email (gói Pro: 12 lần × 300 người/năm) ([nguồn](https://traveljoy.com/blog/post/meet-your-new-marketing-tab)) | **Một phần**: ghi nguồn lead ở Stage 1 (§5) | **Có**: bài viết AA làm cho đại lý (tenant portal CIS) gắn nút dẫn về form của đại lý, kèm ghi nguồn (v1 §3, issue "Attribution"; v2 W1 "D18 CTA"). Chưa có chiến dịch email |

### 1.2 Bán hàng: pipeline, proposal

| Module | Tern | TravelJoy | Spec chị Thư | Thiết kế hiện tại |
|---|---|---|---|---|
| Pipeline theo giai đoạn | **Có**: đại lý tự đặt tên cột; tự chuyển "đang đi" và "đã đi" theo ngày ([nguồn](https://help.tern.travel/en/articles/7929163-best-practices-for-using-trip-statuses-in-tern)) | **Có**: bảng theo giai đoạn, bấm vào một giai đoạn để xử lý cả loạt ([nguồn](https://help.traveljoy.com/hc/en-us/articles/360016247971-Using-the-Dashboard)) | **Có**: 7 giai đoạn + Lost, mỗi bước có điều kiện qua (§4) | **Có**: như spec (v2 §5) |
| Trạng thái "đang chờ ai" | **Chưa có** | **Có**: chờ mình / chờ khách / chờ nhà cung cấp ([nguồn](https://traveljoy.com/blog/post/traveljoy-travel-agency-software-updates-feb-2025)) | **Một phần**: chỉ tiêu "không lead nào im quá 3 ngày" (module 2) | **Chưa có** |
| Proposal kéo thả, thư viện mẫu | **Có**: bảng kế hoạch theo ngày, mẫu theo thư mục, kho ảnh riêng ([nguồn](https://www.tern.travel/advisors)) | **Có**: thư viện mục và cả phần, chia sẻ trong team ([nguồn](https://traveljoy.com/blog/post/product-updates-crm-groups-proposals-and-more)) | **Có**: builder dựng riêng, cắm vào CRM (§1, §9) | **Một phần**: builder bản đồ fork từ TripPlanner (v2.2 S4); chưa thiết kế thư viện mẫu |
| Khách tự chọn phương án | **Có**: khối phương án, chọn hạng phòng, thêm dịch vụ; giá tự cập nhật ([nguồn](https://help.tern.travel/en/articles/7929166-using-option-blocks-to-present-your-client-with-choices)) | **Có**: nhóm phương án chọn một hoặc chọn nhiều ([nguồn](https://traveljoy.com/blog/post/travel-advisor-itinerary-maker-now-offers-options)) | **Có**: chọn theo ngày, luật phụ thuộc, giá và chỗ trống sống, không cần đăng nhập (module 3) | **Có** (v2 §5) |
| Giá và chỗ trống sống từ kho hàng | **Một phần**: tour qua Project Expedition, dữ liệu du thuyền ([nguồn](https://help.tern.travel/en/articles/12683769-project-expedition-tours)) | **Một phần**: 300 nghìn khách sạn, Viator, du thuyền; ăn hoa hồng 8–12% ([nguồn](https://traveljoy.com/blog/post/how-to-search-quote-and-book-on-traveljoy)) | **Có**: hàng AA, giá net, giữ chỗ và xác nhận (§1, §9) | **Có**: API B2B của Booking. Booking chưa có code phần này, cần 6–7 issue (v2 §8) |
| Proposal dạng tin nhắn hoặc PDF | **Một phần**: xuất PDF tuỳ chỉnh ([nguồn](https://www.tern.travel/updates/your-itinerary-pdfs-exactly-how-you-want-them.html)) | **Chưa có** | **Có**: email hoặc tin WhatsApp ngắn, kèm link chọn (module 4) | **Có** (v2 §5) |
| Biết khách đã mở proposal | **Có**: biết ai xem, lúc nào ([nguồn](https://www.tern.travel/updates/see-who-opened-your-itinerary-and-when.html)) | **Một phần**: chỉ với form: gửi, mở, ký, kèm IP ([nguồn](https://traveljoy.com/blog/post/traveljoy-travel-agency-software-updates-feb-2025)) | **Một phần**: có kế hoạch đo sự kiện (§11.7) | **Chưa có**: đã có bảng sự kiện `crm.metric_event` để làm nền (v2 §5) |

### 1.3 Thu tiền và giao dịch vụ

| Module | Tern | TravelJoy | Spec chị Thư | Thiết kế hiện tại |
|---|---|---|---|---|
| Hoá đơn, lịch cọc và trả nốt | **Có**: lịch thanh toán theo từng dịch vụ, xuất hoá đơn PDF ([nguồn](https://help.tern.travel/en/articles/11165214-invoicing)) | **Có**: chia đều phần còn lại, tự tạo việc nhắc ([nguồn](https://traveljoy.com/blog/post/how-travel-advisors-can-handle-payments-like-a-pro-a-recap-of-traveljoys-payments-workshop)) | **Có**: link Stripe, tự nhắc (module 7) | **Có**: Stripe của chính đại lý; ở VN ghi tay (v2 §8) |
| Cách thu tiền thẻ | **Một phần**: khách chỉ **uỷ quyền** thẻ, đại lý tự charge qua nhà cung cấp; Stripe chỉ cho phí dịch vụ, Tern lấy 0,6% ([nguồn](https://help.tern.travel/en/articles/12176225-payments-authorizations-in-tern), [nguồn](https://help.tern.travel/en/articles/8866875-professional-service-fees)) | **Có**: charge thẳng vào ví tiền của trip, trả nhà cung cấp bằng thẻ ảo, phí 3,5–5% + 30c ([nguồn](https://traveljoy.com/pricing), [nguồn](https://help.traveljoy.com/hc/en-us/articles/9484158141076-Pay-your-suppliers)) | **Có**: Stripe (§9) | **Có**: Stripe Connect Standard qua adapter trung lập; AA không giữ tiền (v2.2 §1) |
| Sổ booking: mã xác nhận, giá vốn, giá bán | **Có**: ghi nhanh một booking mà không cần dựng trip ([nguồn](https://help.tern.travel/en/articles/16964995-quick-submit-booking)) | **Một phần**: các trường hoa hồng trên từng dòng hoá đơn ([nguồn](https://www.jess.travel/post/how-to-track-travel-agent-commissions-in-traveljoy)) | **Có**: dòng AA tự điền (module 6) | **Có** (v2 §5) |
| Hoa hồng: dự kiến, đã nhận, đối soát | **Có**: đối soát bảng kê, AI đọc bảng kê, chia hoa hồng, trả cho nhân viên (gói agency) ([nguồn](https://help.tern.travel/en/articles/12904145-commission-reconciliation-overview)) | **Có**: báo cáo theo nhà cung cấp; đối soát bảng kê và trả team từ 07/2026 ([nguồn](https://help.traveljoy.com/hc/en-us/articles/360016090912-Commissions-Sales-Reports)) | **Một phần**: chỉ dự kiến / đã nhận / quá hạn (module 13) | **Một phần**: như spec |
| Danh bạ nhà cung cấp | **Có**: hạng mục, điều khoản huỷ, gộp, nhập hàng loạt ([nguồn](https://help.tern.travel/en/articles/10715150-managing-agency-suppliers)) | **Một phần**: chỉ là danh bạ để trả tiền ([nguồn](https://help.traveljoy.com/hc/en-us/articles/9484158141076-Pay-your-suppliers)) | **Có**: AA là nhà cung cấp mặc định (module 15) | **Có** (v2 §5) |
| Bảo hiểm du lịch trong app | **Có**: báo giá 5 hãng; khách từ chối thì ký giấy từ chối ([nguồn](https://help.tern.travel/en/collections/4012761-trip-planning)) | **Có**: Faye, Arch RoamRight, hoa hồng 24% ([nguồn](https://traveljoy.com/blog/post/how-to-search-quote-and-book-on-traveljoy)) | **Một phần**: chỉ một trường "travel insurance" ở Stage 3 (§5) | **Một phần**: như spec |
| Đặt tour theo đoàn | **Có**: trip mẹ và trip con cho từng nhóm, khách tự đăng ký ([nguồn](https://help.tern.travel/en/articles/10059452-a-guide-to-group-trip-functionality)) | **Có**, mạnh: một link gồm lịch trình + form + thanh toán, xếp phòng, mã giảm giá ([nguồn](https://traveljoy.com/blog/post/how-to-book-group-travel-like-a-pro-traveljoys-first-groups-workshop)) | **Chưa có** | **Chưa có** |
| Ký điện tử điều khoản và waiver | **Một phần**: ô ký trong form, có ghi giờ ([nguồn](https://help.tern.travel/en/articles/9670279-can-i-add-an-e-signature-to-my-forms)) | **Có**: ký trong form, nhật ký ghi cả IP ([nguồn](https://help.traveljoy.com/hc/en-us/articles/360016308711-Send-forms-to-collect-client-details-signed-agreements-and-authorizations)) | **Có**: hãng bảo hiểm phải chấp nhận (module 12) | **Một phần**: có adapter, Dev chạy bản giả; nhà cung cấp chờ chị Thư chọn (v2.2 S3, Q6) |
| Gửi thông tin khách cho AA ops, tự xoá | **Chưa có** | **Chưa có** | **Có**: module 8 | **Có** (v2 §5) |

### 1.4 Liên lạc, tự động hoá, AI

| Module | Tern | TravelJoy | Spec chị Thư | Thiết kế hiện tại |
|---|---|---|---|---|
| Hộp thư email | **Có**: đồng bộ hai chiều Google/Microsoft, theo dõi mở và click, hẹn giờ gửi, mẫu có biến ([nguồn](https://help.tern.travel/en/articles/9015404-an-introduction-to-email-in-tern)) | **Một phần**: chỉ gửi đi bằng địa chỉ của đại lý, không đọc hộp thư ([nguồn](https://help.traveljoy.com/hc/en-us/articles/360028239552-Connect-your-Google-Mail-account-to-TravelJoy)) | **Có**: đồng bộ hai chiều (module 5) | **Một phần**: đại lý chuyển tiếp mail vào CRM, CRM gửi ra bằng Gmail/Outlook của đại lý; đã ghi là lệch spec (v2 §5, §8) |
| WhatsApp, SMS | **Chưa có**: chỉ chat trong app khách ([nguồn](https://apps.apple.com/us/app/-/id6476008962)) | **Một phần**: SMS là add-on $49/tháng cho 1.000 tin; không có WhatsApp ([nguồn](https://traveljoy.com/premium.html)) | **Có**: module 9 | **Có**: WhatsApp + SMS; Messenger/IG để sau (v2.2 S7) |
| Việc cần làm (task) và mẫu task | **Có**: hạn tương đối theo ngày đi, nhắc qua email ([nguồn](https://help.tern.travel/en/articles/7929158-an-introduction-to-tasks-in-tern)) | **Có**: thêm danh sách task vào trip "trong 3 cú bấm", tối đa 30 task ([nguồn](https://help.traveljoy.com/hc/en-us/articles/360016089212-Create-a-task-list-template)) | **Có**: task theo mẫu quy trình (§7) | **Có** (v1 §8.2) |
| Quy trình tự động | **Có**: chạy theo giai đoạn, hạn trả tiền, ngày đi/về, ngày đặc biệt; gửi mail, tạo task, đổi trạng thái, chạy AI ([nguồn](https://help.tern.travel/en/articles/15025814-mastering-workflows-and-automations-in-tern)) | **Có**, chỉ từ gói Pro: tự nhắc form, proposal, thanh toán ([nguồn](https://help.traveljoy.com/hc/en-us/articles/40442701359764-Set-up-automated-proposal-reminders)) | **Có**: module 10 | **Có** (v2 §5) |
| Tag tự kích hoạt quy trình | **Có** ([nguồn](https://help.tern.travel/en/articles/9524583-how-to-add-contact-tags-and-use-automation-to-auto-apply-workflows-for-specific-tags)) | **Có**: tag của trip tự thêm danh sách task ([nguồn](https://traveljoy.com/blog/post/product-updates-smarter-forms-easier-approvals-and-more)) | **Chưa có** | **Chưa có** |
| Nhắc sinh nhật, kỷ niệm, hộ chiếu sắp hết hạn | **Có**: mẫu "Client Care", nhắc hộ chiếu trước 200 ngày ([nguồn](https://help.tern.travel/en/articles/11404393-contact-workflows-and-automations)) | **Có** ([nguồn](https://help.traveljoy.com/hc/en-us/articles/36032853714324-Send-automated-birthday-anniversary-or-passport-expiration-emails-to-your-clients)) | **Chưa có** | **Chưa có** |
| AI soạn nháp, người duyệt mới gửi | **Có**: soạn theo giọng văn của đại lý, mọi thay đổi do AI phải bấm chấp nhận, không gửi số hộ chiếu cho model ([nguồn](https://help.tern.travel/en/articles/14182386-ai-chat-for-notes-and-crm)) | **Một phần**: Copilot sửa proposal, gói Pro 50 lượt/tháng ([nguồn](https://traveljoy.com/blog/post/create-client-ready-itineraries-in-minutes-with-itinerary-copilot)) | **Có**: chỉ dùng dữ liệu đã lọc, bắt buộc duyệt (module 14) | **Có**: lọc thông tin cá nhân trước khi gọi AI, AI tắt mặc định, trần $2/đại lý/tháng (v2 §7.3) |
| AI đọc tài liệu nhà cung cấp, hộ chiếu | **Có**: đọc PDF/email thành lịch trình; đọc mail xác nhận và gợi ý thêm booking; đọc ảnh hộ chiếu Mỹ ([nguồn](https://help.tern.travel/en/articles/14183098-inbox-intelligence)) | **Có**: Magic Importer, Magic Email (dưới 40 giây), đọc hộ chiếu ([nguồn](https://traveljoy.com/ai.html)) | **Chưa có** | **Chưa có** |
| AI ghi biên bản cuộc gọi, gợi ý khách cũ | **Có**: Notetaker cho Zoom/Meet/Teams, bản tóm tắt trước cuộc gọi ([nguồn](https://help.tern.travel/en/articles/14182360-ai-notetaker)) | **Một phần**: danh sách khách cũ "sắp muốn đi tiếp" ([nguồn](https://traveljoy.com/ai.html)) | **Chưa có** | **Chưa có** |

### 1.5 Trải nghiệm khách, quản trị, nền tảng

| Module | Tern | TravelJoy | Spec chị Thư | Thiết kế hiện tại |
|---|---|---|---|---|
| Cổng khách, app khách | **Có**: web và app iOS; báo chuyến bay; khách duyệt, chọn, uỷ quyền thẻ; có mức quyền; phải tạo tài khoản ([nguồn](https://help.tern.travel/en/articles/8694749-traveler-access-permissions)) | **Một phần**: app iOS/Android xem offline, không có push, chỉ ở Mỹ; trên web khách làm qua các link ([nguồn](https://help.traveljoy.com/hc/en-us/articles/21439262542484-Send-our-app-for-itineraries-to-your-clients)) | **Có**: một link cho mọi thứ, không cần đăng nhập (module 11) | **Có**: web, link + mã OTP; không có app điện thoại (v2 §5) |
| Báo cáo cho đại lý | **Có**: hoa hồng, doanh số, KPI; tự tạo báo cáo nếu mua Tern Pro ([nguồn](https://help.tern.travel/en/collections/15412483-reporting)) | **Có**: hoa hồng và doanh số; không có phễu chuyển đổi ([nguồn](https://help.traveljoy.com/hc/en-us/articles/360016090912-Commissions-Sales-Reports)) | **Có**: tỉ lệ chuyển theo giai đoạn, biên lợi nhuận, nguồn lead, phương án khách chọn (module 16) | **Có**: bản cơ bản trước, bản đầy đủ sau (v2 §5) |
| Vai trò trong đại lý, ẩn lợi nhuận | **Có**: Owner / Admin / Collaborator (không thấy tài chính) / Agent; bật tắt quyền xem thẻ theo người ([nguồn](https://help.tern.travel/en/articles/9621179-what-is-the-difference-between-agency-roles-in-tern-owner-admin-collaborator-agent)) | **Có**: Owner / Team member / Assistant ([nguồn](https://help.traveljoy.com/hc/en-us/articles/360028239792-Introduction-to-TravelJoy-teams-and-assistants)) | **Có**: owner / agent / assistant, assistant không thấy biên lợi nhuận (F4) | **Có**: cờ `margin_visible` (v1 §8.2) |
| Nhân viên nghỉ không mang khách theo | **Có**: "Agency-managed", chuyển chủ khách ([nguồn](https://help.tern.travel/en/articles/12861208-agency-managed-contacts-trips)) | **Một phần**: chuyển trip cho người khác, không đảo lại được ([nguồn](https://help.traveljoy.com/hc/en-us/articles/4409220256148-Refer-a-trip-to-your-team-member)) | **Một phần**: nguyên tắc "dữ liệu khách thuộc đại lý" (§2) | **Chưa có**: bản khảo sát r4 §4 có đề xuất, nhưng chưa vào issue nào |
| Bảo mật, riêng tư | **Một phần**: mã hoá trường hộ chiếu, 2FA ([nguồn](https://help.tern.travel/en/articles/8126635-data-privacy-and-security-in-tern)) | **Một phần**: PCI, 2FA ([nguồn](https://hostagencyreviews.com/travel-agency-software/traveljoy)) | **Có**: F1–F5, đại lý tự xem nhật ký truy cập (§8) | **Có**: hơn mặt bằng thị trường (v2.2 §1) |
| AA hỗ trợ chỉ khi đại lý cho phép | **Chưa có** công bố | **Chưa có** công bố | **Một phần**: F1 ghi "AA cũng không được xem" | **Có**: ba lớp, có hạn, chỉ đọc, ghi vào nhật ký của đại lý (v2.2 §3) |
| Tích hợp ngoài: Zapier, API | **Chưa có**: không API công khai, không Zapier ([nguồn](https://hostagencyreviews.com/travel-agency-software/tern)) | **Một phần**: Zapier 13 trigger, gói Premium hoặc thêm $29/tháng ([nguồn](https://zapier.com/apps/traveljoy/integrations)) | **Chưa có** | **Chưa có** |
| Xuất và xoá dữ liệu | **Một phần**: xuất CSV khách có hộ chiếu ([nguồn](https://help.tern.travel/en/articles/14795473-exporting-contacts-with-passport-data-to-csv)) | **Một phần**: xuất danh bạ nhà cung cấp ([nguồn](https://help.traveljoy.com/hc/en-us/articles/45082755210772-See-what-s-new-with-TravelJoy)) | **Có**: xuất toàn bộ và xoá có kiểm chứng (module 18) | **Có** (v2 §5) |
| Số liệu tổng hợp cho AA (nhóm từ 10 khách) | **Chưa có** | **Chưa có** | **Có**: module 17 | **Có**, làm sau (v2 §5) |
| Nhiều tiền tệ, song ngữ | **Chưa có**: chỉ thị trường Mỹ ([nguồn](https://www.tern.travel/)) | **Một phần**: báo cáo tách theo tiền tệ hoá đơn ([nguồn](https://help.traveljoy.com/hc/en-us/articles/360016090912-Commissions-Sales-Reports)) | **Có**: AUD/USD/VND/EUR (§11.6) | **Có**: EN/VI, 4 tiền tệ, múi giờ (v2 §5) |
| Hướng dẫn đại lý làm quen | **Có**: video 2–8 phút trong app, webinar, AI phỏng vấn để cài đặt, bộ mẫu dùng sẵn "Business in a Box" ([nguồn](https://help.tern.travel/en/articles/16769370-agency-setup-with-the-ai-onboarding-guide), [nguồn](https://www.tern.travel/agencies)) | **Có**: workshop trực tuyến mỗi tuần, lộ trình 3 bước ([nguồn](https://traveljoy.com/blog/post/traveljoy-training-workshops)) | **Một phần**: §11.5 còn để mở | **Một phần**: nhập dữ liệu và mời người dùng (v2 §5) |

---

## 2. Khoảng trống

### 2.1 Cả Tern và TravelJoy đều có, spec và thiết kế của mình chưa có

| # | Tính năng | Vì sao đáng để ý |
|---|---|---|
| G1 | Nhắc ngày đặc biệt: sinh nhật, kỷ niệm, **hộ chiếu sắp hết hạn** | Rẻ. Nhắc hộ chiếu trước chuyến trekking giúp tránh huỷ chuyến. Cả hai bên đều đóng gói sẵn thành mẫu |
| G2 | Đặt tour theo đoàn: một link, xếp phòng, mỗi nhóm một hoá đơn | Đây là điểm mạnh nhất của TravelJoy. Booking của AA đã có lịch khởi hành cố định, nên rất hợp với tour ghép đoàn |
| G3 | AI đọc tài liệu nhà cung cấp và hộ chiếu để tự điền | Với hàng AA thì không cần (dòng AA tự điền). Với hàng của nhà cung cấp khác thì giúp bỏ việc gõ tay |
| G4 | Bảo hiểm du lịch trong app, kèm giấy từ chối có ký | Spec đã có waiver và câu hỏi bảo hiểm ở Stage 3. Đây là bước nối tiếp tự nhiên |
| G5 | Đồng bộ lịch, đặt giờ gọi | Ở Tern nằm ngay trong form nhận yêu cầu |
| G6 | Tag kèm quy trình tự chạy theo tag | Cách nhanh để đại lý tự phân loại (trekking, trăng mật, gia đình) mà không phải cấu hình |
| G7 | Thư viện mẫu cho lịch trình, task, email | Thiết kế mới có mẫu email/WhatsApp và mẫu quy trình; còn thiếu thư viện mục lịch trình |
| G8 | Gộp khách trùng (TravelJoy chỉ gộp trip) | Cần ngay khi đại lý nhập danh bạ cũ |
| G9 | App điện thoại cho khách (xem offline) | Cả hai đều có app. Mình mới có web |
| G10 | Đối soát hoa hồng theo bảng kê, chia cho nhân viên | TravelJoy mới thêm 07/2026. Với hàng AA, đại lý ăn chênh lệch giá chứ không ăn hoa hồng, nên việc này kém quan trọng hơn ở Mỹ |

Chỉ một bên có nhưng đáng cân nhắc:
- **Tern:** biết khách đã mở proposal; nhân viên nghỉ không mang khách theo; email theo dõi mở/click; AI ghi biên bản
  cuộc gọi.
- **TravelJoy:** trạng thái "đang chờ ai"; chiến dịch email; danh sách khách cũ nên chăm lại.

### 2.2 Mình có, họ không có (lợi thế của AA)

| # | Lợi thế | Đối thủ đang làm gì |
|---|---|---|
| E1 | **Hàng AA chạy sống:** giá net, chỗ trống, giữ chỗ và xác nhận; dòng AA tự điền vào sổ booking | Họ chỉ nối với bên thứ ba (Viator, Project Expedition) và ăn hoa hồng. Không ai là nhà cung cấp chính |
| E2 | **Khách tự đổi phương án theo từng ngày**, có luật phụ thuộc, trên hàng thật | Tern có khối phương án và dịch vụ thêm, nhưng giá và chỗ trống không lấy từ kho của chính nhà cung cấp |
| E3 | **Nội dung AA làm sẵn cho đại lý:** tour atoms, bài viết tenant viết lại, blog, LinkedIn, gắn nút dẫn về form của đại lý và ghi nguồn lead | Tern không có marketing. TravelJoy có chiến dịch email nhưng đại lý phải tự viết |
| E4 | **Mô hình B2B:** AA là nhà cung cấp, đại lý giữ khách. AA ops chỉ nhận thông tin chuyến đã chốt, tự xoá sau 90 ngày. AA chỉ xem số liệu gộp (nhóm từ 10 khách) | Không có tương đương |
| E5 | **Riêng tư theo kiến trúc** (F1–F5), lọc thông tin cá nhân trước khi gọi AI, AA chỉ vào hỗ trợ khi đại lý cho phép | Tern chỉ mã hoá trường hộ chiếu. Cả hai không công bố gì về việc nhân viên của họ vào tài khoản khách |
| E6 | **WhatsApp** | Tern không có. TravelJoy chỉ có SMS, trả thêm tiền |
| E7 | **Bốn tiền tệ, song ngữ EN/VI, nhiều múi giờ** | Cả hai làm cho thị trường Mỹ |
| E8 | **Hỏi khách theo giai đoạn** (Stage 1/2/3): Stage 3 chỉ mở khi đã cọc; khung Traveler info cho biết còn thiếu gì | Hai bên hỏi bằng form nhưng không chặn theo giai đoạn |
| E9 | **Proposal dạng tin nhắn ngắn**, luôn cùng giá với bản trực quan | Tern chỉ có PDF |
| E10 | **Xuất toàn bộ và xoá có kiểm chứng** | Cả hai chỉ xuất được một phần |
| E11 | **Miễn phí cho đối tác** | $19–149 mỗi tháng, cộng phí thẻ hoặc phí giao dịch |

---

## 3. Cách làm cho dễ dùng, nên học theo

Xếp theo mức ảnh hưởng tới việc vận hành hằng ngày của đại lý.

| # | Cách làm | Nguồn | Áp vào CRM của mình |
|---|---|---|---|
| U1 | **Trip là một thư mục chứa mọi thứ:** tin nhắn, file, task, ghi chú, hoá đơn. Lead chỉ là trip ở cột đầu tiên | [TravelJoy](https://help.traveljoy.com/hc/en-us/articles/360016089792-Create-and-manage-an-individual-trip), [Tern](https://help.tern.travel/en/articles/7929163-best-practices-for-using-trip-statuses-in-tern) | Thiết kế đã làm vậy. Giữ nguyên, đừng tách thêm "lead" thành đối tượng riêng |
| U2 | **"Đang chờ ai"** (mình / khách / nhà cung cấp) đặt cạnh giai đoạn, biến bảng thành danh sách việc phải làm | [TravelJoy](https://help.traveljoy.com/hc/en-us/articles/360016247971-Using-the-Dashboard) | Thêm vào module 2. Cách này đo trực tiếp được chỉ tiêu "không lead nào im quá 3 ngày" |
| U3 | **Bấm một giai đoạn để xử lý cả loạt**, ví dụ nhắc tất cả proposal đang chờ duyệt | [TravelJoy](https://help.traveljoy.com/hc/en-us/articles/360016247971-Using-the-Dashboard) | Module 2 |
| U4 | **Một form tạo luôn khách và trip**, khử trùng theo email + tên, khai nhiều người đi cùng trong một lần gửi | [Tern](https://help.tern.travel/en/articles/8594104-managing-forms-in-tern) | Module 1. Tránh cách của TravelJoy (mỗi người đi cùng phải tự điền form, phải có email) |
| U5 | **Tag tự kích hoạt quy trình**; áp hàng loạt có hiện trước số bản ghi bị ảnh hưởng | [TravelJoy](https://traveljoy.com/blog/post/product-updates-smarter-forms-easier-approvals-and-more), [Tern](https://www.tern.travel/updates/automated-trip-statuses-new-reports-and-your-agency-back-office-home.html) | Module 10 |
| U6 | **Trạng thái tự chuyển theo ngày**, và nhật ký ghi rõ quy trình nào đã đổi trạng thái | [Tern](https://www.tern.travel/updates/automated-trip-statuses-new-reports-and-your-agency-back-office-home.html) | Spec đã có chuyển theo ngày đi/về. Thêm dòng nhật ký "tự động bởi …" |
| U7 | **Duyệt và trả cọc trong một bước**, hoá đơn tự sinh; khách đi theo luồng phương án → phòng → dịch vụ thêm → bảo hiểm → thanh toán → ký | [TravelJoy](https://traveljoy.com/blog/post/traveljoy-travel-agency-software-updates-feb-2025), [Tern](https://help.tern.travel/en/articles/12176225-payments-authorizations-in-tern) | Module 3 + 7 + 12: gộp thành một luồng trên trang khách |
| U8 | **Nhắc thanh toán gửi cho đại lý trước**, đại lý bật một nút để gửi thẳng cho khách | [TravelJoy](https://help.traveljoy.com/hc/en-us/articles/360051796412-Automatically-send-payment-reminders-to-clients) | Module 7. Đại lý mới dùng thấy an toàn hơn |
| U9 | **AI chỉ đề xuất qua thẻ xem trước**, người bấm chấp nhận mới ghi. Có đồng hồ dùng AI báo ở 75/90/100%; hết hạn mức thì AI dừng, không tính phí vượt | [Tern](https://help.tern.travel/en/articles/14182386-ai-chat-for-notes-and-crm), [Tern](https://help.tern.travel/en/articles/15303956-ai-usage-limits) | Module 14 đã có trần $2. Chỉ cần thêm đồng hồ cho đại lý thấy |
| U10 | **Bản nháp và bản đã gửi tách riêng**, kèm "khách đã xem lúc …" | [Tern](https://help.tern.travel/en/articles/8114228-trip-versioning-on-itineraries), [Tern](https://www.tern.travel/updates/see-who-opened-your-itinerary-and-when.html) | Module 3 đã có version. Thêm sự kiện "đã xem" để tự nhắc |
| U11 | **Ghi chú, tìm kiếm và danh sách task mở được từ mọi màn hình** | [Tern](https://tern.travel/whats-new/q1-2026) | Khung chung của app |
| U12 | **Sao chép nhanh** hộ chiếu, ngày sinh, loyalty từ thanh bên của trip | [TravelJoy](https://traveljoy.com/blog/post/product-updates-faster-invoicing-email-campaigns-and-more) | Làm được, nhưng mỗi lần mở trường F1 phải ghi vào nhật ký F5 |
| U13 | **Trường form đặt tên "Client …" tự ghi vào hồ sơ khách**, nên đại lý thêm trường mà không cần lập trình | [TravelJoy](https://help.traveljoy.com/hc/en-us/articles/360016307211-Create-a-form-template) | Module 1, cho trường tự đặt. Không áp cho trường F1 |
| U14 | **Bộ mẫu dùng sẵn** cho đại lý mới (form, email, quy trình), video ngắn trong app, AI phỏng vấn để cài đặt | [Tern](https://www.tern.travel/agencies), [Tern](https://help.tern.travel/en/articles/16769370-agency-setup-with-the-ai-onboarding-guide) | Phần onboarding (§11.5): nạp sẵn mẫu tiếng Anh/Việt và nội dung AA |

**Không nên học theo** (người dùng than phiền):
- **Không có undo** ([Tern, Host Agency Reviews](https://hostagencyreviews.com/travel-agency-software/tern/reviews)).
- **Rút ngắn ngày đi thì mất giá phòng** ([Tern](https://help.tern.travel/en/articles/8114228-trip-versioning-on-itineraries)).
- **Nhắc thanh toán không phân biệt cọc với trả nốt** ([Tern](https://help.tern.travel/en/articles/15025814-mastering-workflows-and-automations-in-tern)).
- **Chuyển trip cho đồng nghiệp rồi không lấy lại được** ([TravelJoy](https://help.traveljoy.com/hc/en-us/articles/4409220256148-Refer-a-trip-to-your-team-member)).
- **Mỗi khách chỉ lưu một ảnh hộ chiếu** ([TravelJoy](https://help.traveljoy.com/hc/en-us/articles/360047051511-Collect-and-store-client-passport-photos)).

---

## 4. Chi phí và vận hành

### 4.1 Đại lý đang trả đối thủ bao nhiêu

| | Tern | TravelJoy |
|---|---|---|
| Gói cơ bản | $49 mỗi người dùng một tháng nếu trả theo tháng; $35 nếu trả theo quý hoặc năm ([pricing](https://tern.travel/pricing)) | Starter $19/tháng: tối đa 12 trip một năm, không có tự động hoá, không có AI ([pricing](https://traveljoy.com/pricing)) |
| Gói cao hơn | Tính năng agency (đối soát hoa hồng, báo cáo agency) chỉ có từ 3 người dùng. Add-on Tern Pro $19 / $39 / $99 / $149 cho thêm AI và báo cáo tự tạo ([Tern Pro](https://help.tern.travel/en/articles/15292346-tern-pro)) | Pro $39/tháng ($32 nếu trả năm). Premium $79–99/tháng ([premium](https://traveljoy.com/premium.html)) |
| Add-on | Tính AI theo hạn mức chung mỗi tháng; hết hạn mức thì dừng, không tính phí vượt ([AI usage](https://help.tern.travel/en/articles/15303956-ai-usage-limits)) | Zapier $29, SMS $49 (1.000 tin), Copilot ×10 $49, chiến dịch email $29 ([premium](https://traveljoy.com/premium.html)) |
| Phí trên giao dịch | 0,6% trên hoá đơn phí dịch vụ qua Stripe ([service fees](https://help.tern.travel/en/articles/8866875-professional-service-fees)) | Thẻ 3,5% + 30c (Pro) hoặc 5% + 30c (Starter); ACH 1,5–3%. Hoa hồng đặt chỗ trong app 8–24% ([pricing](https://traveljoy.com/pricing)) |
| Ví dụ đại lý 3 người | ≈ $105–147/tháng (ước tính từ giá mỗi người dùng) | ≈ $79–99/tháng (Premium gồm 2 thành viên + 1 trợ lý) |

### 4.2 So với mục tiêu tiết kiệm của AA

- **AA tốn bao nhiêu (theo v2.2 §5, ước tính):**
  - Dev: ≈ $11–18/tháng;
  - lúc chạy thật: ≈ **$7,1** mỗi đại lý một tháng khi có 10 đại lý, **$6,1** khi 50, **$3,7–4,3** khi 200.
  - Chưa tính ký điện tử: $0–250/tháng, tuỳ chị Thư chọn.
- **So sánh:** mức đó chỉ bằng khoảng 5–10% số tiền đại lý đang trả cho Tern hay TravelJoy. "Miễn phí cho đối tác" vẫn
  giữ được.
- **Phí bên thứ ba:** đối thủ thu lại qua add-on (SMS, Zapier) hoặc qua phí thẻ. Thiết kế của mình để đại lý **tự trả
  thẳng** qua tài khoản của họ: Meta tính tiền WhatsApp, Twilio tính SMS, Stripe tính phí thẻ. Cách này giữ AA ở mức
  $0 cho các khoản đó.
- **Đã cố ý không làm, vì tốn tiền hoặc tốn công vận hành (nên giữ):**
  - **Đồng bộ Gmail hai chiều như Tern:** cần đợt kiểm định bảo mật Google (CASA) mỗi năm, khoảng $675–5.400 theo v2.1
    §7.1. Chính Tern cũng phải qua đợt kiểm định của Google (nghiên cứu market-travel-crm §1.2, bản nháp ngoài repo).
  - **App điện thoại riêng:** là một sản phẩm thứ hai phải phát hành và duy trì.
  - **Lưu thẻ để uỷ quyền như Tern:** kéo AA vào phạm vi PCI. Stripe cũng xếp đặt chỗ du lịch vào nhóm rủi ro cao.
  - **AI ghi biên bản cuộc gọi:** tốn tiền xử lý âm thanh, và phải chuyên chở thêm dữ liệu cá nhân.
- **Đáng học từ cách tính tiền của họ:**
  - AI theo hạn mức, hết thì dừng chứ không tính vượt (Tern). Thiết kế đã có trần $2, cùng một ý.
  - TravelJoy bán từng add-on riêng. Nếu sau này cần thu tiền, đây là mẫu "lõi miễn phí, phần thêm trả phí" (xem R11).

---

## 5. Đề xuất bổ sung vào thiết kế CRM (xếp hạng)

Xếp theo giá trị cho đại lý chia cho công làm. "Công" là ước tính số issue. Mục nào là lựa chọn kinh doanh thì ghi
**cần chị Thư quyết**.

| Hạng | Đề xuất | Đưa vào module | Công (ước tính) | Ghi chú |
|---|---|---|---|---|
| R1 | Trạng thái **"đang chờ ai"** và **xử lý hàng loạt theo giai đoạn** trên bảng pipeline (U2, U3) | 2 | 1 issue | Rẻ nhất, lợi lớn nhất cho việc hằng ngày. Đo được chỉ tiêu "lead im quá 3 ngày" |
| R2 | **Nhắc ngày đặc biệt**: hộ chiếu sắp hết hạn (mặc định 200 ngày như Tern), sinh nhật, kỷ niệm. Làm thành trigger mới của quy trình, có mẫu "chăm khách" dùng sẵn (G1) | 10 | 1 issue | Mail sinh nhật là marketing, nên chỉ gửi khi khách đã đồng ý (`contact_consent.marketing` đã có) |
| R3 | **Tag** cho khách và trip, kèm quy trình tự chạy theo tag; áp hàng loạt có hiện trước số bản ghi (G6, U5) | 10 | 1–2 issue | — |
| R4 | **Sự kiện "khách đã xem proposal"**, kèm tự nhắc khi khách xem mà chưa chọn (U10) | 3, 10 | 1 issue | Dùng bảng `crm.metric_event` sẵn có |
| R5 | **Đồng hồ dùng AI** cho đại lý, báo ở 75/90/100% (U9) | 14 | < 1 issue | Bổ sung cho trần $2 sẵn có |
| R6 | **Màn gộp khách trùng**, và nhập dữ liệu theo đợt: khách → quan hệ → chuyến cũ → ghi chú (G8) | Onboarding §11.5 | 1–2 issue | Khử trùng theo blind index đã có. Phần gộp phải gộp cả hai bản mã hoá F1 |
| R7 | **Quan hệ giữa khách** (gia đình, người giới thiệu) tự tạo chiều ngược lại, và **khai nhiều người đi cùng trong một form** (U4) | 1, mô hình dữ liệu | 1–2 issue | "Người giới thiệu" cho luôn số liệu nguồn lead |
| R8 | **Khách thuộc đại lý chứ không thuộc nhân viên**: nhân viên nghỉ thì owner chuyển khách sang người khác, nhân viên không xoá hay mang khách đi được (kiểu "agency-managed" của Tern) | F4 | 1 issue | Khớp nguyên tắc spec §2 "dữ liệu khách thuộc đại lý". Nếu muốn ghi thành điều khoản với đại lý thì **cần chị Thư quyết** |
| R9 | **Thư viện mẫu**: mục lịch trình, danh sách task, mẫu email; nạp sẵn mẫu song ngữ và **nội dung AA** cho đại lý mới (G7, U14) | 3, 10, onboarding | 2 issue | Lấy nội dung từ catalog CIS, tăng lợi thế E3 |
| R10 | **AI đọc xác nhận của nhà cung cấp khác** (PDF/email chuyển tiếp) để gợi ý dòng booking và mục lịch trình; người bấm chấp nhận mới ghi (G3) | 6, 14 | 2–3 issue | Bắt buộc đi qua bộ lọc F3. Chi phí AI tính vào trần sẵn có. **Không** đọc ảnh hộ chiếu ở bản đầu, vì đó là dữ liệu F1 nhạy cảm nhất |
| R11 | **Chia gói**: lõi miễn phí, add-on trả phí (AI nhiều hơn, chiến dịch email, đặt tour theo đoàn) theo mẫu TravelJoy | Mô hình giá | — | **Cần chị Thư quyết.** Gộp vào câu H2 / 1.1 đã gửi |
| R12 | **Đặt tour theo đoàn**: một link gồm lịch trình + form + cọc, mỗi nhóm một trip, xếp phòng, chặn khi hết chỗ (G2) | Module mới | 5–7 issue | **Cần chị Thư quyết:** AA có muốn đại lý bán tour ghép đoàn có lịch khởi hành cố định không? Booking đã có `departure`/`allotment` nên phần hàng có sẵn |
| R13 | **Bảo hiểm du lịch**: báo giá trong app, hoặc tối thiểu là giấy từ chối bảo hiểm có ký (G4) | 7, 12 | 1 issue (chỉ giấy từ chối); 3–5 issue (có báo giá) | **Cần chị Thư quyết:** dùng hãng nào, có lấy hoa hồng không. Có thể hỏi cùng lúc với câu Q6 về waiver |
| R14 | **Chiến dịch email** đơn giản cho đại lý gửi khách của chính họ, chỉ gửi người đã đồng ý, có nút huỷ đăng ký | Module mới | 2–3 issue | **Cần chị Thư quyết:** có hợp với nguyên tắc spec §2 không. AA vẫn không bao giờ gửi cho khách của đại lý. Chi phí SES rất nhỏ |
| R15 | **Đặt giờ gọi trong form** và đồng bộ lịch Google/Outlook (G5) | 1 | 2 issue | Ưu tiên thấp. Cần kiểm lại quyền đọc lịch của Google có kéo theo đợt kiểm định bảo mật hay không (chưa kiểm) |
| R16 | **Xem lịch trình offline** cho khách bằng web app cài được (PWA), thay cho app điện thoại riêng (G9) | 11 | 1–2 issue | Làm sau khi đủ 23 module |

**Không đề xuất làm:**
- đồng bộ Gmail hai chiều (lý do ở §4.2; chỉ làm nếu chị Thư bắt buộc, đúng như câu 6 trong market-travel-crm §9);
- uỷ quyền thẻ kiểu Tern;
- AI ghi biên bản cuộc gọi;
- app điện thoại riêng;
- API công khai hay Zapier trước khi có đại lý thật hỏi tới.

**Ảnh hưởng tới kế hoạch:**
- R1–R10 cộng khoảng **11–16 issue**, gần như không thêm chi phí AWS. Phần lớn ăn vào các đợt D3 (module 1, 2), D6
  (module 10) và D7 (module 14).
- R11–R14 chỉ làm sau khi chị Thư trả lời. Nên gộp vào đợt câu hỏi gửi chị cùng với `thu-questions.md` và v2.2 §9.

---

## 6. Về phương pháp

- **Chỉ dùng nguồn công khai:** trang marketing, bảng giá, trung tâm trợ giúp, changelog, App Store, Zapier và trang
  đánh giá bên thứ ba.
  - Không đăng ký, không đăng nhập, không cào dữ liệu hàng loạt.
  - TravelJoy chặn đọc tự động trang trợ giúp (HTTP 403), nên các ý từ trang đó lấy từ đoạn trích của công cụ tìm kiếm.
  - Ý nào không có nguồn công khai được ghi là suy luận (xem từng bản phân tích).
- **Không chạy công cụ dịch ngược** (reverse engineering) với app của hai bên, vì Điều khoản sử dụng của cả hai cấm
  việc này:
  - **Tern**, mục "Use/Prohibited Activities", bản sửa 19/12/2025
    ([tern.travel/terms-of-service](https://www.tern.travel/terms-of-service)), cấm:
    - "Decompiling, disassembling, reverse engineering, or otherwise attempting to discover the source code, underlying
      algorithms…";
    - "Using automated tools, scripts, or other methods to scrape, data mine, or extract data from the Tern Platform or
      Services".
  - **TravelJoy**, mục "Are there restrictions in how I can use the Services?", cập nhật 06/06/2024
    ([traveljoy.com/terms](https://traveljoy.com/terms)), cấm người dùng nào:
    - "decompiles, reverse engineers, or otherwise attempts to obtain the source code or underlying ideas or
      information of or relating to the Services";
    - "crawls, scrapes, or spiders any page, data, or portion of or relating to the Services or Content".
- **Thời điểm:** các điều khoản trên tôi mở lại ngày 20/10/2026. Giá và tính năng của đối thủ đổi nhanh, ví dụ Tern ra
  changelog mỗi tuần. Nên kiểm lại trước khi trích cho đại lý hay đưa vào tài liệu bán hàng.
