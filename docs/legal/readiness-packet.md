---
id: SEC-04-packet
title: Legal readiness packet
description: Bilingual EN-VI summary for Ms. Thu of the privacy, terms, consent, DPA, sub-processor, erasure, transfer, SLA, support, status page, Vercel plan and AI clause questions, each with options and a proposed answer.
type: explanation
status: draft
owner: nghiep
audience: [owner, cio]
applies_to: [ecosystem]
last_reviewed: 2026-10-24
review_every_days: 90
related: [SEC-04, SEC-04-dpa, SEC-04-dsar, SEC-04-retention, SEC-04-consent-query, AA-886, AA-820, AA-839, AA-877]
---

# Legal readiness packet

## Summary

**EN.** The Trip Planner and the Partner Portal now each have a draft privacy notice and draft terms. The four pages
are online, marked "Draft — pending legal review" and hidden from search engines. Every factual sentence on them
describes what the system does today; the points that need a business or legal answer are marked "[to be confirmed]".
A test on 20/10/2026 showed that when a traveller ticks the consent box, the system stores the answer, the date and time,
and where it came from, and that the copy in the booking system matches. Behind the pages there is now a register of
what personal data is processed and which service providers receive it, a draft data processing agreement for
partners, a deletion procedure and a retention log. Twelve topics below each give the current fact, the options and a
proposed answer. The system runs only on a development environment, and it holds no real traveller or customer data:
every traveller and customer record there was a test or internal entry when checked on 17/10/2026, and the 20/10/2026
consent test used a test address. Staff accounts, alert e-mail recipients and the tour catalog are real data. Whether
to involve a lawyer, and on which topics, is Ms. Thư's call.

**VI.** Trip Planner và Partner Portal mỗi bên đã có bản nháp chính sách quyền riêng tư và bản nháp điều khoản. Bốn trang
đang chạy, có nhãn "Draft — pending legal review" và không cho công cụ tìm kiếm lập chỉ mục. Mỗi câu nêu sự kiện trên
các trang đều mô tả đúng việc hệ thống đang làm; các điểm cần quyết định kinh doanh hoặc pháp lý được đánh dấu
"[to be confirmed]". Lần thử ngày 20/10/2026 cho thấy khi khách tích ô đồng ý, hệ thống lưu câu trả lời, ngày giờ và
nguồn, và bản ghi trong hệ thống đặt tour khớp với bản gốc. Phía sau các trang hiện có một sổ đăng ký dữ liệu cá nhân được
xử lý và các nhà cung cấp dịch vụ nhận dữ liệu, một bản nháp thỏa thuận xử lý dữ liệu cho đối tác, một quy trình xoá dữ
liệu và một sổ ghi các lần xoá theo thời hạn lưu trữ. Mười hai chủ đề dưới đây, mỗi chủ đề nêu hiện trạng, các phương án
và một đề xuất. Hệ thống mới chạy trên môi trường phát triển và chưa có dữ liệu thật của khách du lịch hay khách hàng:
khi kiểm ngày 17/10/2026, mọi bản ghi khách đều là bản ghi thử hoặc nội bộ, và lần thử ngày 20/10/2026 dùng một địa chỉ
thử. Tài khoản nhân viên, người nhận e-mail cảnh báo và danh mục tour là dữ liệu thật. Có cần mời luật sư hay không, và
cho chủ đề nào, là chị Thư quyết định.

| # | Topic / Chủ đề | Proposed answer / Đề xuất |
|---|---|---|
| 1 | Data controller entity / Pháp nhân chịu trách nhiệm dữ liệu | The entity that runs adventure.asia / Pháp nhân đang vận hành adventure.asia |
| 2 | Privacy, cookie and terms wording / Nội dung chính sách và điều khoản | Read Annex A, fill the business points / Đọc Phụ lục A, điền các điểm kinh doanh |
| 3 | Consent capture / Ghi nhận sự đồng ý | Keep one purpose: contact about the trip / Giữ một mục đích: liên hệ về chuyến đi |
| 4 | DPA and service providers / Thỏa thuận xử lý dữ liệu và nhà cung cấp | Use the template; list every provider / Dùng mẫu; liệt kê đủ nhà cung cấp |
| 5 | Records of processing / Sổ đăng ký hoạt động xử lý | Use the provisional register now / Dùng sổ tạm thời ngay |
| 6 | Access and deletion requests / Yêu cầu xem và xoá dữ liệu | Manual procedure now, tested job before real data / Làm tay lúc này, có job đã thử trước khi có dữ liệu thật |
| 7 | Data stored in the US / Dữ liệu lưu ở Mỹ | Keep US hosting, prepare transfer documents / Giữ máy chủ ở Mỹ, chuẩn bị hồ sơ chuyển dữ liệu |
| 8 | Service levels / Cam kết dịch vụ | Response times only until production / Chỉ cam kết thời gian phản hồi tới khi chạy chính thức |
| 9 | Support address / Địa chỉ hỗ trợ | `support@` to a shared mailbox / `support@` về một hộp thư chung |
| 10 | Status page / Trang trạng thái | None until the first paying partner / Chưa làm tới khi có đối tác trả tiền đầu tiên |
| 11 | Vercel plan / Gói Vercel | Pro before the first partner is charged (D-18) / Lên Pro trước lần thu tiền đối tác đầu tiên (D-18) |
| 12 | AI acceptable-use clause / Điều khoản sử dụng AI | A or C: adopt the AI Schedule now (no partners yet); answer needed by 11/11/2026 / A hoặc C: áp dụng Phụ lục AI ngay (chưa có đối tác); cần chị trả lời trước 11/11/2026 |

## 1. Data controller entity

**EN.** *Current fact:* both privacy notices say the legal entity responsible for the data and its registered address
are "[to be confirmed]" (Trip Planner and portal `/privacy` §1). The terms leave the operating entity open the same way.
*Options:* (A) the company that runs adventure.asia and publishes its privacy policy; (B) another group entity, for
example one created for the platform. *Proposed answer:* A, with its full name and registered address, so the notices,
the partner agreement and the DPA name the same party. *Detail:* [register](register.md), section (a).

**VI.** *Hiện trạng:* cả hai trang chính sách ghi pháp nhân chịu trách nhiệm dữ liệu và địa chỉ đăng ký là
"[to be confirmed]" (mục 1 trang `/privacy` của Trip Planner và portal). Trang điều khoản cũng để trống pháp nhân vận
hành. *Phương án:* (A) công ty đang vận hành adventure.asia và đăng chính sách quyền riêng tư ở đó; (B) một pháp nhân khác
trong nhóm, ví dụ pháp nhân lập riêng cho nền tảng. *Đề xuất:* A, kèm tên đầy đủ và địa chỉ đăng ký, để chính sách, hợp
đồng đối tác và thỏa thuận xử lý dữ liệu cùng nêu một bên. *Chi tiết:* [sổ đăng ký](register.md), mục (a).

## 2. Privacy, cookie and terms wording

**EN.** *Current fact:* the four draft pages are live:
`https://aa-tripplanner.vercel.app/privacy`, `https://aa-tripplanner.vercel.app/terms`,
`https://portal.lumiguides.it.com/privacy` and `https://portal.lumiguides.it.com/terms`. They are linked from the site
footers and next to the Trip Planner contact form. Annex A below quotes their full text. On cookies: the Trip Planner
uses one guest cookie (a random token, stored only as a one-way hash) and browser storage for the current trip and the
display theme; the portal uses sign-in cookies only. Neither uses advertising or analytics cookies, and the code
contains no analytics tool. *Options:* (A) Ms. Thư reads Annex A and answers the business points (entity, address, minimum age,
answer time for requests, booking conditions, fees), then decides whether counsel reviews the result; (B) send Annex A
to counsel as it is. Table A.0 lists every open point on the four pages in both languages. *Proposed answer:* A.
*Detail:* Annex A; [register](register.md), "Page copy follow-ups".

**VI.** *Hiện trạng:* bốn trang nháp đang chạy:
`https://aa-tripplanner.vercel.app/privacy`, `https://aa-tripplanner.vercel.app/terms`,
`https://portal.lumiguides.it.com/privacy` và `https://portal.lumiguides.it.com/terms`. Các trang được dẫn link ở chân
trang và ngay cạnh form liên hệ của Trip Planner. Phụ lục A bên dưới trích đầy đủ nội dung. Về cookie: Trip Planner dùng
một cookie khách (mã ngẫu nhiên, hệ thống chỉ lưu bản băm một chiều) và bộ nhớ trình duyệt cho chuyến đi đang soạn và
chế độ sáng/tối; portal chỉ dùng cookie đăng nhập. Không bên nào dùng cookie quảng cáo hay thống kê, và mã nguồn không
có công cụ thống kê nào. *Phương án:* (A) chị Thư đọc Phụ lục A và trả lời các điểm kinh doanh (pháp nhân, địa chỉ, tuổi tối thiểu,
thời hạn trả lời yêu cầu, điều kiện đặt tour, phí), rồi quyết định có nhờ luật sư xem lại hay không; (B) gửi nguyên Phụ
lục A cho luật sư. Bảng A.0 liệt kê song ngữ mọi điểm còn mở trên bốn trang. *Đề xuất:* A. *Chi tiết:* Phụ lục A;
[sổ đăng ký](register.md), mục "Page copy follow-ups".

## 3. Consent capture

**EN.** *Current fact:* the Trip Planner form asks the traveller to agree that an advisor may contact them about the
trip. A test inquiry on 20/10/2026 was followed through three records (the Trip Planner record, the hand-off message, the
booking system customer): each stored consent "yes" with the same date and time, and the booking record names the Trip
Planner as the source. Across all records there were 0 cases of consent without a time, a time without consent, or a
mismatch between the two systems. This consent covers contact about the trip only, not newsletters or other marketing.
*Options:* (A) keep this single purpose; (B) add a second, optional, unticked box for marketing when marketing is
planned. *Proposed answer:* A now, B only when a marketing use exists. *Detail:* [consent capture check](consent-capture-query.md).

**VI.** *Hiện trạng:* form của Trip Planner hỏi khách có đồng ý để tư vấn viên liên hệ về chuyến đi hay không. Một yêu
cầu thử ngày 20/10/2026 được theo dõi qua ba bản ghi (bản ghi Trip Planner, tin nhắn chuyển giao, khách hàng trong hệ thống
đặt tour): cả ba đều lưu "đồng ý" với cùng ngày giờ, và bản ghi đặt tour ghi nguồn là Trip Planner. Trên toàn bộ dữ liệu có
0 trường hợp đồng ý mà không có thời điểm, có thời điểm mà không đồng ý, hoặc hai hệ thống ghi khác nhau. Sự đồng ý này chỉ
dùng để liên hệ về chuyến đi, không dùng cho bản tin hay tiếp thị khác. *Phương án:* (A) giữ một mục đích như hiện nay;
(B) thêm ô thứ hai cho tiếp thị, không bắt buộc và không tích sẵn, khi có kế hoạch tiếp thị. *Đề xuất:* A lúc này, B chỉ
khi có nhu cầu tiếp thị. *Chi tiết:* [kiểm tra ghi nhận đồng ý](consent-capture-query.md).

## 4. DPA template and service providers

**EN.** *Current fact:* a draft data processing agreement for partners is ready for review. It sets out that the
partner is the controller for data it puts into the portal and Adventure Asia is the processor, lists the processor
duties, and has annexes for the processing, the security measures (each marked live or planned) and the service
providers. The register lists the providers found in the code: AWS (hosting, e-mail, sign-in, AI models through Amazon
Bedrock), the AI providers OpenAI and Jev, Sentry (error reports), Vercel (websites), Mapbox (maps), Geoapify,
DataForSEO, Google (photo files), the adventure.asia mail host, and work tools. Jev receives partner content only for a short list of test partners, until a data processing and zero-retention
agreement with Jev is in place; that agreement is an open item. Other open points: whether the AWS resellers
(TrueIDC for the hosting account, eCloudvalley for the AI account) and the model makers behind Bedrock must be listed,
and the contract status of each provider. *Options:* (A) list every provider, including resellers, and remove any that
counsel says are not needed; (B) list only providers that process data directly. *Proposed answer:* A. *Detail:*
[DPA template](dpa-template.md); [register](register.md), section (b).

**VI.** *Hiện trạng:* bản nháp thỏa thuận xử lý dữ liệu cho đối tác đã sẵn sàng để xem. Bản nháp nêu đối tác là bên kiểm
soát dữ liệu họ đưa vào portal và Adventure Asia là bên xử lý, liệt kê nghĩa vụ của bên xử lý, và có các phụ lục về hoạt
động xử lý, biện pháp bảo mật (mỗi biện pháp ghi rõ đang chạy hay mới dự kiến) và nhà cung cấp dịch vụ. Sổ đăng ký liệt kê
các nhà cung cấp tìm thấy trong mã nguồn: AWS (máy chủ, e-mail, đăng nhập, mô hình AI qua Amazon Bedrock), các nhà cung
cấp AI OpenAI và Jev, Sentry (báo lỗi), Vercel (website), Mapbox (bản đồ), Geoapify, DataForSEO, Google (tệp ảnh), nhà
cung cấp hộp thư adventure.asia, và các công cụ làm việc. Jev chỉ nhận nội dung của một danh sách ngắn các đối tác thử, cho tới khi có thỏa thuận xử lý dữ liệu và không lưu dữ
liệu với Jev; thỏa thuận đó là một điểm còn mở. Các điểm mở khác: có phải liệt kê các đại lý bán lại AWS (TrueIDC cho
tài khoản máy chủ, eCloudvalley cho tài khoản AI) và các hãng làm mô hình phía sau Bedrock hay không, và tình trạng hợp đồng
với từng nhà cung cấp. *Phương án:* (A) liệt kê đủ mọi nhà cung cấp, kể cả đại lý bán lại, rồi bỏ bớt những bên luật sư cho
là không cần; (B) chỉ liệt kê các bên trực tiếp xử lý dữ liệu. *Đề xuất:* A. *Chi tiết:* [mẫu thỏa thuận](dpa-template.md);
[sổ đăng ký](register.md), mục (b).

## 5. Records of processing

**EN.** *Current fact:* the register lists eight processing activities: Trip Planner inquiries and consent, the
booking customer record and trip cases, booking notifications and audit, staff accounts, partner accounts, AI content
generation, alert e-mails, and supplier contacts. For each it gives the people concerned, the kinds of data, where the data is stored,
how long it is kept, who receives it and where it goes. It was built by hand from the database structure, so personal
data inside free-text notes may be missed; it will be rebuilt automatically once every personal-data column is tagged
in the database. *Options:* (A) use the provisional register now; (B) wait for the automatic version. *Proposed
answer:* A. *Detail:* [register](register.md), section (a).

**VI.** *Hiện trạng:* sổ đăng ký liệt kê tám hoạt động xử lý: yêu cầu và sự đồng ý trên Trip Planner, hồ sơ khách và
chuyến đi trong hệ thống đặt tour, thông báo và nhật ký kiểm tra của hệ thống đặt tour, tài khoản nhân viên, tài khoản đối
tác, tạo nội dung bằng AI, e-mail cảnh báo, và thông tin liên hệ của nhà cung cấp dịch vụ tour. Mỗi hoạt động ghi rõ người liên quan, loại dữ liệu, nơi lưu, thời gian lưu,
bên nhận và nơi dữ liệu đi tới. Sổ được lập bằng tay từ cấu trúc cơ sở dữ liệu, nên dữ liệu cá nhân nằm trong ghi chú tự do
có thể bị sót; sổ sẽ được lập lại tự động khi mọi cột chứa dữ liệu cá nhân được gắn nhãn trong cơ sở dữ liệu. *Phương án:*
(A) dùng sổ tạm thời ngay; (B) chờ bản tự động. *Đề xuất:* A. *Chi tiết:* [sổ đăng ký](register.md), mục (a).

## 6. Access and deletion requests

**EN.** *Current fact:* requests can be sent to `info@adventure.asia`, as both privacy notices say. A written procedure
exists for checking the person's identity, finding their records in both systems, and deleting them under a counted
dry run that Nghiệp approves first. The records are found by a one-way code (hash) computed from the e-mail address and
then deleted by record number, so the address itself is never written into code, logs or files. Database backups keep a
copy for up to 7 days after a deletion and then expire. It has not been run yet, and a tested deletion job does not exist yet. No real
deletion has happened, and three test records are kept for the first test. Deleting a partner account today only
switches it off; nothing is erased. The time within which a request is answered is "[to be confirmed]" on the pages.
*Options:* (A) use the manual procedure now and have a tested job before real traveller data is stored; (B) build the
job first. *Proposed answer:* A, and choose the answer time (for example [●] days). *Detail:*
[DSAR and erasure runbook](dsar-erasure-runbook.md); [retention log](retention-log.md).

**VI.** *Hiện trạng:* khách có thể gửi yêu cầu tới `info@adventure.asia`, như cả hai trang chính sách đã ghi. Đã có quy
trình viết sẵn để xác minh danh tính, tìm bản ghi của người đó trong cả hai hệ thống, và xoá sau một lần chạy thử có đếm số
dòng mà Nghiệp duyệt trước. Bản ghi được tìm bằng một mã băm một chiều tính từ địa chỉ e-mail rồi xoá theo mã số bản ghi,
nên chính địa chỉ e-mail không bao giờ được ghi vào mã nguồn, nhật ký hay tệp nào. Bản sao lưu cơ sở dữ liệu còn giữ dữ
liệu tối đa 7 ngày sau khi xoá rồi tự hết hạn. Quy trình này chưa chạy lần nào, và chưa có job xoá đã được thử. Chưa có lần xoá thật nào; ba
bản ghi thử được giữ lại cho lần thử đầu tiên. Xoá tài khoản đối tác hiện chỉ là tắt tài khoản, chưa xoá dữ liệu. Thời hạn
trả lời yêu cầu đang để "[to be confirmed]" trên các trang. *Phương án:* (A) dùng quy trình làm tay ngay, và có job đã thử
trước khi lưu dữ liệu khách thật; (B) làm job trước. *Đề xuất:* A, và chọn thời hạn trả lời (ví dụ [●] ngày). *Chi tiết:*
[quy trình yêu cầu và xoá dữ liệu](dsar-erasure-runbook.md); [sổ ghi lưu trữ](retention-log.md).

## 7. Data stored in the United States

**EN.** *Current fact:* the database and servers are in the United States (AWS, us-west-1), and most service providers
are US companies (AWS, Vercel, Mapbox, Sentry, OpenAI); Vercel and Mapbox serve pages and maps from locations close to
the visitor. Two points go beyond "United States": the AI accounts call Amazon Bedrock through "global" routing, which
can process a request (trip contents, tour text, never a name or contact detail) in a region outside the US; and the
Vercel functions that carry the Trip Planner contact form run in Vercel's default region, which is not pinned
("[to be confirmed]"). The pages leave the
transfer safeguards "[to be confirmed]". The S245 research notes, for counsel to confirm: Vietnam's personal data
protection law (Law 91/2025/QH15) and Decree 356/2025/ND-CP took effect on 01/01/2026 and require a transfer impact
assessment, also for offshore cloud hosting, filed within 60 days of the transfer starting; for EU partners, the
standard contractual clauses (Module 2, controller to processor) apply to US hosting; for Australian partners, APP 8
on cross-border disclosure applies. This packet makes no legal claim of its own on these points. *Options:* (A) keep
US hosting and prepare the transfer documents the chosen regimes require; (B) consider a region closer to customers
later, which changes cost and setup. *Proposed answer:* A. *Detail:*
[`04-economics-compliance-security.md`](../audits/2026-10-20-S245-tenant-crm/research/04-economics-compliance-security.md) §4.

**VI.** *Hiện trạng:* cơ sở dữ liệu và máy chủ đặt tại Mỹ (AWS, us-west-1), và phần lớn nhà cung cấp là công ty Mỹ
(AWS, Vercel, Mapbox, Sentry, OpenAI); Vercel và Mapbox phục vụ trang web và bản đồ từ điểm gần người xem. Có hai điểm
vượt ra ngoài "tại Mỹ": các tài khoản AI gọi Amazon Bedrock qua chế độ định tuyến "global", có thể xử lý một yêu cầu (nội
dung chuyến đi, nội dung tour, không bao giờ có tên hay thông tin liên hệ) ở một vùng ngoài nước Mỹ; và các hàm Vercel
chuyển form liên hệ của Trip Planner chạy ở vùng mặc định của Vercel, chưa được cố định ("[to be confirmed]"). Các trang đang để biện pháp bảo vệ khi chuyển dữ liệu
là "[to be confirmed]". Nghiên cứu phiên S245 ghi lại, để luật sư xác nhận: Luật Bảo vệ dữ liệu cá nhân của Việt Nam (Luật
91/2025/QH15) và Nghị định 356/2025/NĐ-CP có hiệu lực từ 01/01/2026, yêu cầu đánh giá tác động chuyển dữ liệu ra nước ngoài,
kể cả khi dùng máy chủ đám mây ở nước ngoài, nộp trong vòng 60 ngày kể từ khi bắt đầu chuyển; với đối tác ở EU, áp dụng
điều khoản hợp đồng mẫu (Module 2, bên kiểm soát sang bên xử lý) cho việc lưu ở Mỹ; với đối tác ở Úc, áp dụng nguyên tắc
APP 8 về chuyển dữ liệu ra nước ngoài. Tài liệu này không tự đưa ra nhận định pháp lý nào về các điểm trên. *Phương án:*
(A) giữ máy chủ ở Mỹ và chuẩn bị hồ sơ chuyển dữ liệu theo các luật được chọn; (B) cân nhắc chuyển sang vùng gần khách hơn
về sau, việc này đổi chi phí và cách cài đặt. *Đề xuất:* A. *Chi tiết:*
[`04-economics-compliance-security.md`](../audits/2026-10-20-S245-tenant-crm/research/04-economics-compliance-security.md) mục 4.

## 8. Service levels

**EN.** *Current fact:* the portal terms leave service levels and support hours "[to be confirmed]" (§8). Internally,
incidents are handled by severity: SEV1 (a product is down for customers or partners, or data is exposed or lost) is
handled at once, at any hour, Ms. Thư is told within 30 minutes and affected partners within 2 hours; SEV2 (a feature is
broken with a workaround) is handled the same working day; SEV3 (internal only) goes to the backlog. *Options:* (A)
until production, promise response times only, based on these levels, and no uptime percentage; (B) promise an uptime
percentage with service credits, which needs the production setup first. *Proposed answer:* A now, B when production
exists. *Detail:* [incident response](../ops/incident-response.md), "Severity".

**VI.** *Hiện trạng:* điều khoản portal để cam kết dịch vụ và giờ hỗ trợ là "[to be confirmed]" (mục 8). Trong nội bộ,
sự cố được xử lý theo mức độ: SEV1 (sản phẩm ngừng hoạt động với khách hoặc đối tác, hoặc dữ liệu bị lộ hay mất) được xử
lý ngay, bất kể giờ nào, chị Thư được báo trong 30 phút và đối tác bị ảnh hưởng được báo trong 2 giờ; SEV2 (một chức năng
hỏng nhưng có cách làm tạm) được xử lý trong cùng ngày làm việc; SEV3 (chỉ ảnh hưởng nội bộ) được đưa vào danh sách việc.
*Phương án:* (A) tới khi chạy chính thức, chỉ cam kết thời gian phản hồi theo các mức trên, không cam kết tỷ lệ hoạt động;
(B) cam kết tỷ lệ hoạt động kèm bồi hoàn, việc này cần hạ tầng chính thức trước. *Đề xuất:* A lúc này, B khi có hạ tầng
chính thức. *Chi tiết:* [xử lý sự cố](../ops/incident-response.md), mục "Severity".

## 9. Support address

**EN.** *Current fact:* the pages give `info@adventure.asia` for questions and privacy requests. The adventure.asia
mailboxes are hosted by DreamHost, which therefore receives any personal data in those e-mails. *Options:* (A) keep
`info@adventure.asia`; (B) create `support@` and forward it into the team's issue tracker (Linear) for triage: the
tracker's free plan has a limit on open items, and e-mail content would put traveller data into the tracker, which would
then have to be listed as a service provider; (C) create `support@` as an alias to a shared mailbox, and let staff open
a tracker item by hand without personal data. *Proposed answer:* C. *Detail:* [register](register.md), section (b),
DreamHost and Linear rows.

**VI.** *Hiện trạng:* các trang ghi `info@adventure.asia` cho câu hỏi và yêu cầu về quyền riêng tư. Hộp thư adventure.asia
do DreamHost lưu trữ, nên DreamHost nhận mọi dữ liệu cá nhân trong các e-mail đó. *Phương án:* (A) giữ
`info@adventure.asia`; (B) tạo `support@` và chuyển tiếp vào công cụ quản lý việc của nhóm (Linear) để phân loại: gói miễn
phí có giới hạn số việc đang mở, và nội dung e-mail sẽ đưa dữ liệu khách vào công cụ đó, khi ấy phải liệt kê nó là nhà cung
cấp dịch vụ; (C) tạo `support@` là bí danh chuyển về một hộp thư chung, nhân viên tự tạo việc trên công cụ khi cần và không
chép dữ liệu cá nhân. *Đề xuất:* C. *Chi tiết:* [sổ đăng ký](register.md), mục (b), dòng DreamHost và Linear.

## 10. Status page

**EN.** *Current fact:* there is no public status page. The goal is a $0 option with no new AWS service. *Options:*
(A) a free hosted status page from a status-page provider, which adds a provider to the list; (B) a page built by
scheduled GitHub Actions (for example Upptime) in a **public** repository, where Actions minutes are free; in the
private main repository it would use the 2,000 free minutes a month that other work also uses; (C) no status page until
the first paying partner. *Proposed answer:* C, then A or B in a public repository. *Detail:* this section.

**VI.** *Hiện trạng:* chưa có trang trạng thái công khai. Mục tiêu là phương án 0 USD và không thêm dịch vụ AWS mới.
*Phương án:* (A) dùng trang trạng thái miễn phí của một nhà cung cấp, việc này thêm một nhà cung cấp vào danh sách; (B) dựng
trang bằng GitHub Actions chạy theo lịch (ví dụ Upptime) trong một kho mã **công khai**, nơi phút chạy Actions miễn phí;
nếu đặt trong kho mã riêng tư chính thì sẽ dùng chung 2.000 phút miễn phí mỗi tháng với các việc khác; (C) chưa làm trang
trạng thái tới khi có đối tác trả tiền đầu tiên. *Đề xuất:* C, sau đó A hoặc B trong kho mã công khai. *Chi tiết:* mục này.

## 11. Vercel plan

**EN.** *Current fact:* the websites run on Vercel's free Hobby plan. Vercel describes Hobby as "for personal,
non-commercial use", per the S245 research. The engineering decision already taken (D-18) is: Hobby until the first
paying partner, then Pro. Pro costs 20 USD per member per month, plus usage above the amounts the plan includes.
*Options:* (A) move to Pro before the first partner is charged, as D-18 says; (B) move earlier, when the first partner
starts using the portal even if it pays nothing, which the S245 research suggests because Hobby is non-commercial.
Any new spend needs Nghiệp's approval (DM-10.7). *Proposed answer:* A. *Detail:*
[`04-economics-compliance-security.md`](../audits/2026-10-20-S245-tenant-crm/research/04-economics-compliance-security.md) lines 15 and 49.

**VI.** *Hiện trạng:* các website chạy trên gói Hobby miễn phí của Vercel. Theo nghiên cứu phiên S245, Vercel mô tả gói
Hobby là "cho mục đích cá nhân, phi thương mại". Quyết định kỹ thuật đã có (D-18) là: dùng Hobby tới khi có đối tác trả
tiền đầu tiên, sau đó chuyển lên Pro. Gói Pro giá 20 USD mỗi thành viên mỗi tháng, cộng phí theo mức dùng vượt phần gói đã
bao gồm. *Phương án:* (A) chuyển lên Pro trước lần thu tiền đối tác đầu tiên, đúng như D-18; (B) chuyển sớm hơn, ngay khi
đối tác đầu tiên bắt đầu dùng portal dù chưa trả tiền, như nghiên cứu S245 gợi ý vì Hobby là gói phi thương mại.
Mọi khoản chi mới cần Nghiệp duyệt (DM-10.7). *Đề xuất:* A. *Chi tiết:*
[`04-economics-compliance-security.md`](../audits/2026-10-20-S245-tenant-crm/research/04-economics-compliance-security.md) dòng 15 và 49.

## 12. AI acceptable-use clause

**EN.** *Current fact:* Anthropic's Usage Policy takes effect on 12/11/2026 (the live text was re-read on 24/10/2026)
and reaches partners whose content is written with Claude through Amazon Bedrock. The full AI Schedule for the partner
terms is at Draft v0.2. Since the AA-820 portal change, the portal terms §3 carry a short summary of it (Annex A.4),
still under the "Draft — pending legal review" banner. There are no real or paying partners yet, so nobody needs a
notice: each partner accepts the Schedule when it joins, with its partner agreement. The agency CRM does not call
Claude yet; the Schedule must be part of the agency terms before it does. Ms. Thư's answer is needed by 11/11/2026, one
day before the policy takes effect. *Options:* (A) adopt the Schedule as written: the portal summary is already live
before 11/11, the Schedule is attached to every partner agreement at onboarding, and a lawyer's review is optional and
her call; (B) a lawyer reviews the Schedule first, and the portal keeps the summary marked as a draft until then;
(C) adopt it now as in A, and have a lawyer review it before the first paying partner. *Proposed answer:* A or C. With
no partners yet, adopting now costs nothing and covers the 12/11 date; C adds a review before the first partner pays.
*Detail:* [AI acceptable-use clause draft](tenant-terms-ai-clause-draft.md): where each part goes (§0), the Schedule
(§2) and 14 questions for a lawyer (§6).

**VI.** *Hiện trạng:* Chính sách sử dụng của Anthropic có hiệu lực từ 12/11/2026 (bản đang đăng đã được đọc lại ngày
24/10/2026) và áp dụng cho các đối tác có nội dung được viết bằng Claude qua Amazon Bedrock. Phụ lục AI đầy đủ cho điều
khoản đối tác đang ở bản Draft v0.2. Từ thay đổi AA-820 trên portal, mục 3 của điều khoản portal có một bản tóm tắt ngắn
của phụ lục này (Phụ lục A.4), vẫn nằm dưới nhãn "Draft — pending legal review". Hiện chưa có đối tác thật hay đối tác
trả tiền, nên không cần gửi thông báo cho ai: mỗi đối tác chấp nhận phụ lục khi tham gia, cùng với hợp đồng đối tác. CRM
cho đại lý chưa gọi Claude; phụ lục phải nằm trong điều khoản cho đại lý trước khi CRM gọi Claude. Cần chị Thư trả lời
trước ngày 11/11/2026, một ngày trước khi chính sách có hiệu lực. *Phương án:* (A) áp dụng phụ lục như bản hiện tại: bản
tóm tắt trên portal đã có trước 11/11, phụ lục được đính kèm mọi hợp đồng đối tác khi đối tác tham gia, còn việc nhờ luật
sư xem là tùy chị quyết định; (B) luật sư xem phụ lục trước, và portal giữ bản tóm tắt ở trạng thái bản nháp cho tới
lúc đó; (C) áp dụng ngay như phương án A, và nhờ luật sư xem trước khi có đối tác trả tiền đầu tiên. *Đề xuất:* A hoặc C.
Vì chưa có đối tác, áp dụng ngay không tốn gì và kịp mốc 12/11; phương án C thêm một lần xem của luật sư trước khi đối
tác đầu tiên trả tiền. *Chi tiết:* [bản nháp điều khoản sử dụng AI](tenant-terms-ai-clause-draft.md): từng phần đặt ở đâu
(mục 0), phụ lục (mục 2) và 14 câu hỏi cho luật sư (mục 6).

## Annex A: current text of the four pages

**EN.** The text below is copied from the page source as rendered, at AA-TripPlanner-Web commit `c497489` (2026-10-20)
and AA-CIS-App commit `6e00458d` (2026-10-20), except A.4 §3, which is the AA-820 text of 24/10/2026. Each page shows
the banner "Draft — pending legal review". The Trip Planner pages show the version "Draft v0.1"; the two portal pages
show "Draft v0.2" (24 October 2026) since the AA-820 change. Links are shown as their text. If a page changes after
those commits, the live page wins.

**VI.** Nội dung dưới đây được chép từ mã nguồn trang, đúng như hiển thị, tại commit `c497489` (20/10/2026) của
AA-TripPlanner-Web và commit `6e00458d` (20/10/2026) của AA-CIS-App, trừ mục 3 của A.4 là nội dung AA-820 ngày
24/10/2026. Mỗi trang có nhãn "Draft — pending legal review". Hai trang Trip Planner ghi phiên bản "Draft v0.1"; hai
trang portal ghi "Draft v0.2" (24 October 2026) từ thay đổi AA-820. Link được ghi bằng chữ hiển thị. Nếu trang thay đổi sau các commit trên, trang đang chạy là bản đúng.
Nội dung trang giữ nguyên tiếng Anh như trên website. Bảng A.0 dưới đây liệt kê song ngữ mọi điểm "[to be confirmed]"
trên bốn trang, để chị Thư trả lời mà không cần đọc hết bản tiếng Anh.

### A.0 Points to be confirmed on the four pages / Các điểm cần xác nhận trên bốn trang

**EN.** Every "[to be confirmed]" point in A.1 to A.4, with the packet topic that proposes an answer.
**VI.** Mọi điểm "[to be confirmed]" trong A.1 đến A.4, kèm chủ đề trong gói này có đề xuất trả lời.

| Page, section / Trang, mục | Point (EN) | Điểm cần xác nhận (VI) | Topic / Chủ đề |
|---|---|---|---|
| A.1 §1, A.3 §1 | Data controller entity and registered address | Pháp nhân chịu trách nhiệm dữ liệu và địa chỉ đăng ký | 1 |
| A.2 §1, A.4 §1 | Operating legal entity | Pháp nhân vận hành | 1 |
| A.1 §4, A.3 §4 | Legal basis for each use of the data | Cơ sở pháp lý cho từng mục đích sử dụng dữ liệu | 2 |
| A.1 §6 | Full list of service providers, kept in a register | Danh sách đầy đủ nhà cung cấp dịch vụ, ghi trong sổ đăng ký | 4 |
| A.3 §5 | Full list of AI providers | Danh sách đầy đủ nhà cung cấp AI | 4 |
| A.1 §7, A.3 §7 | Safeguards for transfers outside the person's country | Biện pháp bảo vệ khi chuyển dữ liệu ra ngoài nước của người dùng | 7 |
| A.1 §8 | Retention periods: the customer record after the enquiry or booking ends; trips never sent | Thời hạn lưu: hồ sơ khách sau khi yêu cầu hoặc đặt tour kết thúc; chuyến đi chưa gửi | 2, 5 |
| A.3 §8 | Retention of publish records and the admin log; account data and content after the account ends | Thời hạn lưu hồ sơ đăng bài và nhật ký quản trị; dữ liệu tài khoản và nội dung sau khi tài khoản kết thúc | 2, 5 |
| A.1 §9, A.3 §9 | Time to answer a request; the right to complain to a data protection authority | Thời hạn trả lời yêu cầu; quyền khiếu nại tới cơ quan bảo vệ dữ liệu | 6 |
| A.1 §11 | Minimum age | Tuổi tối thiểu | 2 |
| A.2 §2 | Booking conditions | Điều kiện đặt tour | 2 |
| A.2 §7 | Limits of liability, warranties and consumer rights | Giới hạn trách nhiệm, bảo đảm và quyền của người tiêu dùng | 2 |
| A.2 §8, A.4 §9 | Governing law and competent courts (A.4 §9 also limits of liability) | Luật áp dụng và tòa án có thẩm quyền (A.4 mục 9 gồm cả giới hạn trách nhiệm) | 2 |
| A.3 §10 | Data processing agreement between the partner and Adventure Asia | Thỏa thuận xử lý dữ liệu giữa đối tác và Adventure Asia | 4 |
| A.4 intro | How the terms relate to the signed partner agreement | Quan hệ giữa điều khoản này và hợp đồng đối tác đã ký | 2 |
| A.4 §3 | Approval of the AI acceptable-use summary (draft; no longer marked [to be confirmed]) | Duyệt bản tóm tắt điều khoản sử dụng AI (bản nháp; không còn ghi [to be confirmed]) | 12 |
| A.4 §5 | Notice periods, termination, and what happens to the content afterwards | Thời hạn báo trước, chấm dứt, và nội dung được xử lý thế nào sau đó | 2 |
| A.4 §6 | Ownership of generated content; licence to the catalog tours | Quyền sở hữu nội dung tạo ra; giấy phép dùng tour trong danh mục | 2 |
| A.4 §7 | Plans, fees and payment terms | Gói dịch vụ, phí và điều khoản thanh toán | 2 |
| A.4 §8 | Service levels and support hours | Cam kết dịch vụ và giờ hỗ trợ | 8 |

### A.1 Trip Planner: Privacy notice (`/privacy`)

This notice explains what personal data the Adventure Asia Trip Planner (this website) collects, why, who receives it
and what you can ask us to do with it. It covers the Trip Planner only. Adventure Asia's company-wide policy is at
adventure.asia/privacy-policy.

**1. Who we are.** The Trip Planner is run by Adventure Asia. The legal entity responsible for your data (the data
controller) and its registered address are [to be confirmed]. For any privacy question or request, write to
`info@adventure.asia`.

**2. What we collect.** You can browse tours and build a trip without giving us your name or contact details.

- **Your trip.** The destinations, stops, activities, number of days and travellers you choose, and the order of your
  days. It is saved under a random guest identifier, not under your name.
- **What you type in the planner search.** Used to find matching places and activities. Please do not type personal
  details into the search box.
- **Your contact details, only when you send a trip to an advisor.** Your full name, your phone number and/or email
  address, and whether you agreed that an advisor may contact you, with the date and time you agreed.
- **Technical data.** Our hosting providers process your IP address, browser type and the pages you request in order to
  deliver the site and keep it secure.

**3. Cookies and browser storage.** We use only what the planner needs to work. We do not use advertising or analytics
cookies.

- **Guest cookie** (set on the planner page only): a random token that proves a saved trip is yours. It cannot be read
  by scripts on the page, and it lasts up to 400 days, renewed each time you use the planner. We store only a one-way
  hash of it.
- **Browser storage:** the random ids of your current trip, so a reload restores it, and your light or dark display
  choice.

Clearing your browser data removes them; you then start a new trip.

**4. How we use your data.**

- To build, save and show your trip (providing the service you asked for).
- To pass your trip and contact details to an Adventure Asia advisor who contacts you about that trip. We do this only
  after you tick the consent box on the form, and we record that consent with its date, time and source.
- Your consent covers contact about the trip you sent. We do not use it for newsletters or other marketing.
- To keep the service secure and prevent abuse.

The legal basis for each use under the laws that apply to you is [to be confirmed].

**5. AI features.** The planner uses AI models to write the day-by-day description of your trip and to match your
search text to places. These models run on Amazon Bedrock (Amazon Web Services). We send them the contents of your trip
(places, activities, days) and your search text, never your name or contact details. Every itinerary is reviewed by an
Adventure Asia advisor before you book.

**6. Who receives your data.**

- **Adventure Asia advisors**, through Adventure Asia's booking system, which receives the trips you send and keeps the
  customer record. Advisors are notified of a new inquiry by email.
- **Amazon Web Services** — hosting, database, the AI models above (Amazon Bedrock) and the notification emails (Amazon
  SES).
- **Vercel** — hosts and delivers this website.
- **Mapbox** — map images and the interactive map. Your browser loads them from Mapbox, which receives your IP address
  and the map area you view.

We do not sell your personal data. The full list of service providers will be kept in a register [to be confirmed].

**7. Where your data is stored.** Our database and servers are in the United States (Amazon Web Services). Vercel and
Mapbox serve the site and maps from locations close to you. The safeguards for transfers outside your country are [to be
confirmed].

**8. How long we keep it.** Retention periods are being set and are [to be confirmed]. The current plan: the copy of
your contact details inside the message that sends your trip to the booking system is removed after 90 days, and the
customer record in the booking system is kept while your enquiry or booking is active and then for a period [to be
confirmed]. Trips that were never sent [retention to be confirmed].

**9. Your rights.** You can ask us to show you the data we hold about you, correct it, delete it, or stop contacting
you, and you can withdraw your consent at any time. Write to `info@adventure.asia`. The time within which we answer, and
your right to complain to a data protection authority, are [to be confirmed].

**10. Security.** The site uses encrypted connections (HTTPS). Our database is not reachable from the internet, and
access to it is limited to the systems that need it. No method is perfectly secure; if a breach affects your data we
will inform you as the law requires.

**11. Children.** The Trip Planner is not meant for children. The minimum age is [to be confirmed].

**12. Changes to this notice.** We will publish changes on this page with a new date. See also our Terms of use.

### A.2 Trip Planner: Terms of use (`/terms`)

These terms apply when you use the Adventure Asia Trip Planner (this website). By using it you accept them. If you do
not agree, please do not use the site.

**1. What the Trip Planner is.** The Trip Planner is a free tool for exploring Adventure Asia tours and shaping a trip
idea day by day. It is run by Adventure Asia; the operating legal entity is [to be confirmed].

**2. A trip plan is not a booking.**

- A trip you build or send to an advisor is an enquiry. Nothing is reserved or paid, and no contract for travel services
  is made through this site.
- An Adventure Asia advisor reviews your trip and contacts you to confirm logistics, availability and price. A booking
  exists only when you agree to it with Adventure Asia under separate booking conditions [booking conditions to be
  confirmed].
- Prices, availability and itineraries shown on the site are indicative and can change.

**3. AI-assisted content.** Some descriptions on the site, including the day-by-day text of your trip, are written with
the help of AI and are labelled as such. They can contain mistakes. Do not rely on them for travel, visa, health or
safety decisions; your advisor confirms the details before anything is booked.

**4. Using the site.**

- Give accurate contact details when you send a trip, and only your own.
- Use the site only for planning your own travel, and in line with the law.
- Do not try to access other people's trips, overload or disrupt the service, or copy its content in bulk with
  automated tools.

We may limit or block access that breaks these rules.

**5. Content and maps.** The tours, texts, photos and design of the site belong to Adventure Asia or its licensors. Maps
are provided by Mapbox and OpenStreetMap contributors under their own terms. You may use the site for your personal,
non-commercial trip planning.

**6. Availability and changes.** The site is under active development. Features can change, and the site may be
unavailable at times. We may update these terms; the date at the top of the page shows the current version.

**7. Liability.** Limits of liability, warranties and consumer rights under the laws that apply to you are [to be
confirmed].

**8. Governing law.** The governing law and competent courts are [to be confirmed].

**9. Contact.** Questions about these terms: `info@adventure.asia`. How we handle personal data is described in our
Privacy notice.

### A.3 Partner Portal: Privacy notice (`/privacy`)

This notice explains what personal data the Adventure Asia Partner Portal collects about partner businesses and the
people who use it, why, and who receives it. Adventure Asia's company-wide policy is at adventure.asia/privacy-policy.

**1. Who we are.** The Partner Portal is run by Adventure Asia. The legal entity responsible for your data (the data
controller) and its registered address are [to be confirmed]. Privacy questions and requests: `info@adventure.asia`.

**2. What we collect.**

- **Partner account.** Your business name, plan and account status, and the API key you sign in with. We check the key
  on our server; the browser then holds a sign-in session.
- **Brand settings and content.** The brand voice and settings you enter, the tour rewrites and social or blog pieces
  generated for you, and your edits.
- **Channel connections.** The details you give us to publish to your own channels (for example a WordPress site or a
  Facebook Page).
- **Activity records.** Each AI model call (provider, model, cost, time, partner and job), each publish and unpublish
  (piece, channel, post id, status, time, and whether your account or an Adventure Asia admin acted), and an admin log
  of changes to partner accounts.
- **Technical data.** IP address, browser type and request logs, processed by our hosting providers and our security
  systems.

**3. Cookies.** The portal uses only sign-in cookies, which scripts on the page cannot read. They hold your session and
expire after 24 hours or when you sign out. We do not use advertising or analytics cookies.

**4. How we use your data.**

- To run your account and produce the content you ask for.
- To publish or unpublish a piece on your channels when you tell us to.
- To support you, keep the service secure, and enforce the partner terms.
- To measure our own costs and service quality.

The legal basis for each use is [to be confirmed].

**5. AI processing.** Content is generated by AI models: Claude (Anthropic) through Amazon Bedrock, and other AI
providers that review and score the drafts. They receive tour content, your brand settings and the instructions for each
piece. Our policy is not to send personal data to these models and not to store any in our AI call records, so please do
not enter personal data about other people in brand settings or content. The full list of AI providers is [to be
confirmed].

**6. Who receives your data.**

- **Adventure Asia staff**, for support and moderation (they can suspend an account or unpublish a post that Adventure
  Asia published for you).
- **Amazon Web Services** — hosting, database, Amazon Bedrock.
- **Vercel** — hosts and delivers the portal pages.
- **AI providers** as described above.
- **Your channels** (for example WordPress or Meta), when you publish to them.

We do not sell personal data.

**7. Where your data is stored.** Our database and servers are in the United States (Amazon Web Services). The
safeguards for transfers outside your country are [to be confirmed].

**8. How long we keep it.**

- AI model call records: 180 days.
- Security logs: 365 days.
- Publish records and the admin log: a period will be set before production [to be confirmed].
- Account data and content: while your account is active, then [to be confirmed].

**9. Your rights.** You can ask to see, correct or delete personal data we hold about you. Write to `info@adventure.asia`.
Response times and your right to complain to a data protection authority are [to be confirmed].

**10. Data about your own customers.** If you put personal data of other people into the portal, you are responsible
for having the right to do so. A data processing agreement between you and Adventure Asia is [to be confirmed].

**11. Changes to this notice.** We will publish changes on this page with a new date. See also the partner terms.

### A.4 Partner Portal: Partner terms (`/terms`)

These terms apply to partner businesses that use the Adventure Asia Partner Portal and its API. They will form part of,
or sit next to, the partner agreement you sign with Adventure Asia [relationship to be confirmed].

**1. The service.** The portal gives you Adventure Asia catalog tours rewritten in your brand voice, social and blog
pieces about those tours, and tools to export them or publish them to your own channels. The operating legal entity is
[to be confirmed].

**2. Your account and API key.**

- Keep your API key secret. Activity under your key is treated as yours.
- Tell us at once at `info@adventure.asia` if you think the key is known to someone else, so we can revoke it.

**3. AI-generated content and acceptable use.**

- Content is generated with AI and can contain mistakes. The portal shows this at review, publish and export: "This
  content was generated with AI. Review it before publishing; you are responsible for what you publish."
- The content is written with models from third-party providers, including Anthropic's Claude through Amazon Web
  Services. You must follow their usage policies, including the Anthropic Usage Policy and the AWS Acceptable Use
  Policy, as well as these terms.
- You must not use the portal or its content for:
  - fake reviews, ratings or testimonials, or quotes and stories presented as coming from customers who did not give
    them;
  - invented personas, sockpuppet accounts, or content attributed to a real person who did not write or approve it;
  - astroturfing, or networks of websites or accounts that look independent but are not;
  - hiding sponsorship or a commercial relationship, or removing a disclosure the law or a channel requires;
  - seeding search engines or AI systems with content that misrepresents its origin, authorship or independence;
  - spam, or posting meant to get around the publishing limit;
  - false or misleading information, in particular about visas and entry rules, health, safety, prices or
    availability;
  - advice on insurance, finance, visas or other high-risk matters, unless a qualified person reviews it before it is
    delivered and the person receiving it is told that AI was used;
  - getting around Adventure Asia's content checks, limits or other safeguards.
- If the law or a channel's rules require content to be labelled as AI-generated, you add that label.
- You review each piece before it is published, and you are its publisher. Telling Adventure Asia to publish a piece,
  in the portal or through the API, confirms that you have reviewed it.
- Adventure Asia may hold, rewrite or decline to generate or publish content that breaks these rules. Unpublishing and
  suspension are covered in sections 4 and 5.

**4. Publishing to your channels.**

- Adventure Asia publishes a piece to your channels only when you tell it to publish that piece, using the access you
  connected. The post appears under your name.
- There is a daily limit on the number of posts Adventure Asia publishes for you.
- You can unpublish your posts. Adventure Asia can also unpublish a post it published for you, for example when it
  breaks these terms.

**5. Suspension and ending the service.** Adventure Asia may suspend an account, which stops its API access and
publishing at once, for example to protect the service or when these terms are broken. Notice periods, termination and
what happens to your content afterwards are [to be confirmed].

**6. Content rights.** Who owns the generated content and the licence to the catalog tours are [to be confirmed].

**7. Plans and fees.** Plans, fees and payment terms are [to be confirmed].

**8. Availability.** The portal is under active development; features can change and the service may be unavailable at
times. Service levels and support hours are [to be confirmed].

**9. Liability and governing law.** Limits of liability, the governing law and the competent courts are [to be
confirmed].

**10. Contact.** Questions: `info@adventure.asia`. How we handle personal data is described in the privacy notice.
