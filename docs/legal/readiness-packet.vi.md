---
id: SEC-04-packet
title: Bộ hồ sơ sẵn sàng pháp lý
description: Tóm tắt cho chủ doanh nghiệp về các câu hỏi chính sách quyền riêng tư, điều khoản, sự đồng ý, thỏa thuận xử lý dữ liệu, nhà cung cấp, xoá dữ liệu, chuyển dữ liệu, cam kết dịch vụ, hỗ trợ, trang trạng thái, gói Vercel và điều khoản AI, mỗi câu kèm phương án và đề xuất.
type: explanation
status: draft
owner: nghiep
audience: [owner, cio]
applies_to: [ecosystem]
last_reviewed: 2026-10-28
review_every_days: 90
related: [SEC-04, SEC-04-dpa, SEC-04-dsar, SEC-04-retention, SEC-04-consent-query, AA-886, AA-820, AA-839, AA-877]
lang: vi
translation_of: docs/legal/readiness-packet.md
---

# Bộ hồ sơ sẵn sàng pháp lý

Đây là bản tiếng Việt của [readiness-packet.md](readiness-packet.md). Bản tiếng Anh là bản gốc.

## Tóm tắt

Trip Planner và Partner Portal mỗi bên đã có bản nháp chính sách quyền riêng tư và bản nháp điều khoản. Bốn trang
đang chạy, có nhãn "Draft — pending legal review" và không cho công cụ tìm kiếm lập chỉ mục. Mỗi câu nêu sự kiện trên
các trang đều mô tả đúng việc hệ thống đang làm; các điểm cần quyết định kinh doanh hoặc pháp lý được đánh dấu
"[to be confirmed]". Lần thử ngày 20/10/2026 cho thấy khi khách tích ô đồng ý, hệ thống lưu câu trả lời, ngày giờ và
nguồn, và bản ghi trong hệ thống đặt tour khớp với bản gốc. Phía sau các trang hiện có một sổ đăng ký dữ liệu cá nhân
được xử lý và các nhà cung cấp dịch vụ nhận dữ liệu, một bản nháp thỏa thuận xử lý dữ liệu cho đối tác, một quy trình
xoá dữ liệu và một sổ ghi các lần xoá theo thời hạn lưu trữ. Mười hai chủ đề dưới đây, mỗi chủ đề nêu hiện trạng, các
phương án và một đề xuất. Hệ thống mới chạy trên môi trường phát triển và chưa có dữ liệu thật của khách du lịch hay
khách hàng: khi kiểm ngày 17/10/2026, mọi bản ghi khách đều là bản ghi thử hoặc nội bộ, và lần thử ngày 20/10/2026 dùng
một địa chỉ thử. Tài khoản nhân viên, người nhận e-mail cảnh báo và danh mục tour là dữ liệu thật. Có cần mời luật sư
hay không, và cho chủ đề nào, là chủ doanh nghiệp quyết định.

| # | Chủ đề | Đề xuất |
|---|---|---|
| 1 | Pháp nhân chịu trách nhiệm dữ liệu | Pháp nhân đang vận hành adventure.asia |
| 2 | Nội dung chính sách, cookie và điều khoản | Đọc Phụ lục A, điền các điểm kinh doanh |
| 3 | Ghi nhận sự đồng ý | Giữ một mục đích: liên hệ về chuyến đi |
| 4 | Thỏa thuận xử lý dữ liệu và nhà cung cấp | Dùng mẫu; liệt kê đủ nhà cung cấp |
| 5 | Sổ đăng ký hoạt động xử lý | Dùng sổ tạm thời ngay |
| 6 | Yêu cầu xem và xoá dữ liệu | Làm tay lúc này, có job đã thử trước khi có dữ liệu thật |
| 7 | Dữ liệu lưu ở Mỹ | Giữ máy chủ ở Mỹ, chuẩn bị hồ sơ chuyển dữ liệu |
| 8 | Cam kết dịch vụ | Chỉ cam kết thời gian phản hồi tới khi chạy chính thức |
| 9 | Địa chỉ hỗ trợ | `support@` về một hộp thư chung |
| 10 | Trang trạng thái | Chưa làm tới khi có đối tác trả tiền đầu tiên |
| 11 | Gói Vercel | Lên Pro trước lần thu tiền đối tác đầu tiên (D-18) |
| 12 | Điều khoản sử dụng AI | A hoặc C: áp dụng Phụ lục AI ngay (chưa có đối tác); cần trả lời trước 11/11/2026 |

## 1. Pháp nhân chịu trách nhiệm dữ liệu

*Hiện trạng:* cả hai trang chính sách ghi pháp nhân chịu trách nhiệm dữ liệu và địa chỉ đăng ký là
"[to be confirmed]" (mục 1 trang `/privacy` của Trip Planner và portal). Trang điều khoản cũng để trống pháp nhân vận
hành. *Phương án:* (A) công ty đang vận hành adventure.asia và đăng chính sách quyền riêng tư ở đó; (B) một pháp nhân
khác trong nhóm, ví dụ pháp nhân lập riêng cho nền tảng. *Đề xuất:* A, kèm tên đầy đủ và địa chỉ đăng ký, để chính sách,
hợp đồng đối tác và thỏa thuận xử lý dữ liệu cùng nêu một bên. *Chi tiết:* [sổ đăng ký](register.md), mục (a).

## 2. Nội dung chính sách, cookie và điều khoản

*Hiện trạng:* bốn trang nháp đang chạy:
`https://aa-tripplanner.vercel.app/privacy`, `https://aa-tripplanner.vercel.app/terms`,
`https://portal.lumiguides.it.com/privacy` và `https://portal.lumiguides.it.com/terms`. Các trang được dẫn link ở chân
trang và ngay cạnh form liên hệ của Trip Planner. Phụ lục A bên dưới trích đầy đủ nội dung. Về cookie: Trip Planner dùng
một cookie khách (mã ngẫu nhiên, hệ thống chỉ lưu bản băm một chiều), cookie đăng nhập chỉ khi khách đăng nhập, và bộ nhớ
trình duyệt cho chuyến đi đang soạn và chế độ sáng/tối; portal chỉ dùng cookie đăng nhập. Không bên nào dùng cookie
quảng cáo hay thống kê, và mã nguồn không có công cụ thống kê nào. *Phương án:* (A) chủ doanh nghiệp đọc Phụ lục A và
trả lời các điểm kinh doanh (pháp nhân, địa chỉ, tuổi tối thiểu, thời hạn trả lời yêu cầu, điều kiện đặt tour, phí),
rồi quyết định có nhờ luật sư xem lại hay không; (B) gửi nguyên Phụ lục A cho luật sư. Bảng A.0 liệt kê mọi điểm còn
mở trên bốn trang. *Đề xuất:* A. *Chi tiết:* Phụ lục A; [sổ đăng ký](register.md), mục "Page copy follow-ups".

## 3. Ghi nhận sự đồng ý

*Hiện trạng:* form của Trip Planner hỏi khách có đồng ý để tư vấn viên liên hệ về chuyến đi hay không. Một yêu cầu thử
ngày 20/10/2026 được theo dõi qua ba bản ghi (bản ghi Trip Planner, tin nhắn chuyển giao, khách hàng trong hệ thống đặt
tour): cả ba đều lưu "đồng ý" với cùng ngày giờ, và bản ghi đặt tour ghi nguồn là Trip Planner. Trên toàn bộ dữ liệu có
0 trường hợp đồng ý mà không có thời điểm, có thời điểm mà không đồng ý, hoặc hai hệ thống ghi khác nhau. Sự đồng ý này
chỉ dùng để liên hệ về chuyến đi, không dùng cho bản tin hay tiếp thị khác. *Phương án:* (A) giữ một mục đích như hiện
nay; (B) thêm ô thứ hai cho tiếp thị, không bắt buộc và không tích sẵn, khi có kế hoạch tiếp thị. *Đề xuất:* A lúc này,
B chỉ khi có nhu cầu tiếp thị. *Chi tiết:* [kiểm tra ghi nhận đồng ý](consent-capture-query.md).

## 4. Thỏa thuận xử lý dữ liệu và nhà cung cấp

*Hiện trạng:* bản nháp thỏa thuận xử lý dữ liệu cho đối tác đã sẵn sàng để xem. Bản nháp nêu đối tác là bên kiểm soát
dữ liệu họ đưa vào portal và Adventure Asia là bên xử lý, liệt kê nghĩa vụ của bên xử lý, và có các phụ lục về hoạt động
xử lý, biện pháp bảo mật (mỗi biện pháp ghi rõ đang chạy hay mới dự kiến) và nhà cung cấp dịch vụ. Sổ đăng ký liệt kê các
nhà cung cấp tìm thấy trong mã nguồn: AWS (máy chủ, e-mail, đăng nhập, mô hình AI qua Amazon Bedrock), các nhà cung cấp
AI OpenAI và Jev, Sentry (báo lỗi), Vercel (website), Mapbox (bản đồ), Geoapify, DataForSEO, Google (tệp ảnh), nhà cung
cấp hộp thư adventure.asia, và các công cụ làm việc. Jev chỉ nhận nội dung của một danh sách ngắn các đối tác thử, cho tới
khi có thỏa thuận xử lý dữ liệu và không lưu dữ liệu với Jev; thỏa thuận đó là một điểm còn mở. Các điểm mở khác: có phải
liệt kê các đại lý bán lại AWS (TrueIDC cho tài khoản máy chủ, eCloudvalley cho tài khoản AI) và các hãng làm mô hình phía
sau Bedrock hay không, và tình trạng hợp đồng với từng nhà cung cấp. *Phương án:* (A) liệt kê đủ mọi nhà cung cấp, kể cả
đại lý bán lại, rồi bỏ bớt những bên luật sư cho là không cần; (B) chỉ liệt kê các bên trực tiếp xử lý dữ liệu.
*Đề xuất:* A. *Chi tiết:* [mẫu thỏa thuận](dpa-template.md); [sổ đăng ký](register.md), mục (b).

## 5. Sổ đăng ký hoạt động xử lý

*Hiện trạng:* sổ đăng ký liệt kê tám hoạt động xử lý: yêu cầu và sự đồng ý trên Trip Planner, hồ sơ khách và chuyến đi
trong hệ thống đặt tour, thông báo và nhật ký kiểm tra của hệ thống đặt tour, tài khoản nhân viên, tài khoản đối tác, tạo
nội dung bằng AI, e-mail cảnh báo, và thông tin liên hệ của nhà cung cấp dịch vụ tour. Mỗi hoạt động ghi rõ người liên
quan, loại dữ liệu, nơi lưu, thời gian lưu, bên nhận và nơi dữ liệu đi tới. Sổ được lập bằng tay từ cấu trúc cơ sở dữ
liệu, nên dữ liệu cá nhân nằm trong ghi chú tự do có thể bị sót; sổ sẽ được lập lại tự động khi mọi cột chứa dữ liệu cá
nhân được gắn nhãn trong cơ sở dữ liệu. *Phương án:* (A) dùng sổ tạm thời ngay; (B) chờ bản tự động. *Đề xuất:* A.
*Chi tiết:* [sổ đăng ký](register.md), mục (a).

## 6. Yêu cầu xem và xoá dữ liệu

*Hiện trạng:* khách có thể gửi yêu cầu tới `info@adventure.asia`, như cả hai trang chính sách đã ghi. Đã có quy trình
viết sẵn để xác minh danh tính, tìm bản ghi của người đó trong cả hai hệ thống, và xoá sau một lần chạy thử có đếm số dòng
mà trưởng nhóm kỹ thuật duyệt trước. Bản ghi được tìm bằng một mã băm một chiều tính từ địa chỉ e-mail rồi xoá theo mã số
bản ghi, nên chính địa chỉ e-mail không bao giờ được ghi vào mã nguồn, nhật ký hay tệp nào. Bản sao lưu cơ sở dữ liệu còn
giữ dữ liệu tối đa 7 ngày sau khi xoá rồi tự hết hạn. Hệ thống nội dung đã có job xoá với bước chạy thử có đếm số dòng.
Phần xoá đối tác của job đã được thử một lần trên môi trường phát triển, ngày 23/10/2026, với một đối tác giả lập: chạy
thử, duyệt, xoá và kiểm lại đều đạt. Phần xoá khách du lịch chưa chạy lần nào, và các script xoá của hệ thống đặt tour và
Trip Planner chưa được viết. Chưa có lần xoá thật nào; ba bản ghi thử được giữ lại cho lần thử đầu tiên với khách du lịch.
Khi kết thúc một tài khoản đối tác, bước đầu chỉ là tắt tài khoản; dữ liệu được xoá sau, trong một bước riêng do trưởng
nhóm kỹ thuật duyệt. Thời hạn trả lời yêu cầu đang để "[to be confirmed]" trên các trang. *Phương án:* (A) dùng quy trình
làm tay ngay, và hoàn tất phần xoá khách du lịch đã thử trước khi lưu dữ liệu khách thật; (B) hoàn tất phần xoá khách du
lịch trước. *Đề xuất:* A, và chọn thời hạn trả lời (ví dụ [●] ngày). *Chi tiết:*
[quy trình yêu cầu và xoá dữ liệu](dsar-erasure-runbook.md); [sổ ghi lưu trữ](retention-log.md).

## 7. Dữ liệu lưu ở Mỹ

*Hiện trạng:* cơ sở dữ liệu và máy chủ đặt tại Mỹ (AWS, us-west-1), và phần lớn nhà cung cấp là công ty Mỹ (AWS, Vercel,
Mapbox, Sentry, OpenAI); Vercel và Mapbox phục vụ trang web và bản đồ từ điểm gần người xem. Có một điểm vượt ra ngoài
"tại Mỹ": tài khoản AI gọi Amazon Bedrock qua chế độ định tuyến "global", có thể xử lý một yêu cầu (nội dung chuyến đi,
nội dung tour, không bao giờ có tên hay thông tin liên hệ) ở một vùng ngoài nước Mỹ. Các hàm Vercel chuyển form liên hệ
của Trip Planner chạy ở vùng San Francisco của Vercel (`sfo1`) từ ngày 28/10/2026, và partner portal nay chạy trên AWS ở
us-west-1. Các trang đang để biện pháp bảo vệ khi chuyển dữ liệu là "[to be confirmed]". Nghiên cứu phiên S245 ghi lại,
để luật sư xác nhận: Luật Bảo vệ dữ liệu cá nhân của Việt Nam (Luật 91/2025/QH15) và Nghị định 356/2025/NĐ-CP có hiệu
lực từ 01/01/2026, yêu cầu đánh giá tác động chuyển dữ liệu ra nước ngoài, kể cả khi dùng máy chủ đám mây ở nước ngoài,
nộp trong vòng 60 ngày kể từ khi bắt đầu chuyển; với đối tác ở EU, áp dụng điều khoản hợp đồng mẫu (Module 2, bên kiểm
soát sang bên xử lý) cho việc lưu ở Mỹ; với đối tác ở Úc, áp dụng nguyên tắc APP 8 về chuyển dữ liệu ra nước ngoài. Tài
liệu này không tự đưa ra nhận định pháp lý nào về các điểm trên. *Phương án:* (A) giữ máy chủ ở Mỹ và chuẩn bị hồ sơ
chuyển dữ liệu theo các luật được chọn; (B) cân nhắc chuyển sang vùng gần khách hơn về sau, việc này đổi chi phí và cách
cài đặt. *Đề xuất:* A. *Chi tiết:*
[`04-economics-compliance-security.md`](../audits/2026-10-20-S245-tenant-crm/research/04-economics-compliance-security.md) mục 4.

## 8. Cam kết dịch vụ

*Hiện trạng:* điều khoản portal để cam kết dịch vụ và giờ hỗ trợ là "[to be confirmed]" (mục 8). Trong nội bộ, sự cố
được xử lý theo mức độ: SEV1 (sản phẩm ngừng hoạt động với khách hoặc đối tác, hoặc dữ liệu bị lộ hay mất) được xử lý
ngay, bất kể giờ nào, chủ doanh nghiệp được báo trong 30 phút và đối tác bị ảnh hưởng được báo trong 2 giờ; SEV2 (một
chức năng hỏng nhưng có cách làm tạm) được xử lý trong cùng ngày làm việc; SEV3 (chỉ ảnh hưởng nội bộ) được đưa vào danh
sách việc. *Phương án:* (A) tới khi chạy chính thức, chỉ cam kết thời gian phản hồi theo các mức trên, không cam kết tỷ
lệ hoạt động; (B) cam kết tỷ lệ hoạt động kèm bồi hoàn, việc này cần hạ tầng chính thức trước. *Đề xuất:* A lúc này, B
khi có hạ tầng chính thức. *Chi tiết:* [xử lý sự cố](../ops/incident-response.md), mục "Severity".

## 9. Địa chỉ hỗ trợ

*Hiện trạng:* các trang ghi `info@adventure.asia` cho câu hỏi và yêu cầu về quyền riêng tư. Hộp thư adventure.asia do
DreamHost lưu trữ, nên DreamHost nhận mọi dữ liệu cá nhân trong các e-mail đó. *Phương án:* (A) giữ
`info@adventure.asia`; (B) tạo `support@` và chuyển tiếp vào công cụ quản lý việc của nhóm (Linear) để phân loại: gói
miễn phí có giới hạn số việc đang mở, và nội dung e-mail sẽ đưa dữ liệu khách vào công cụ đó, khi ấy phải liệt kê nó là
nhà cung cấp dịch vụ; (C) tạo `support@` là bí danh chuyển về một hộp thư chung, nhân viên tự tạo việc trên công cụ khi
cần và không chép dữ liệu cá nhân. *Đề xuất:* C. *Chi tiết:* [sổ đăng ký](register.md), mục (b), dòng DreamHost và
Linear.

## 10. Trang trạng thái

*Hiện trạng:* chưa có trang trạng thái công khai. Mục tiêu là phương án 0 USD và không thêm dịch vụ AWS mới.
*Phương án:* (A) dùng trang trạng thái miễn phí của một nhà cung cấp, việc này thêm một nhà cung cấp vào danh sách; (B)
dựng trang bằng GitHub Actions chạy theo lịch (ví dụ Upptime) trong một kho mã **công khai**, nơi phút chạy Actions miễn
phí. Kho mã chính chỉ công khai tới khi hết giai đoạn viết mã; khi kho trở lại riêng tư, trang trạng thái đặt ở đó sẽ dùng
chung 2.000 phút miễn phí mỗi tháng với các việc khác; (C) chưa làm trang trạng thái tới khi có đối tác trả tiền đầu
tiên. *Đề xuất:* C, sau đó A hoặc B trong kho mã công khai. *Chi tiết:* mục này.

## 11. Gói Vercel

*Hiện trạng:* Trip Planner, trang quản trị của hệ thống nội dung và trang quản trị đặt tour chạy trên gói Hobby miễn phí
của Vercel. Partner portal đã chuyển từ Vercel sang AWS trong tháng 10/2026; dự án Vercel cũ của portal chỉ được giữ làm
phương án quay lui tới ngày 03/11/2026. Theo nghiên cứu phiên S245, Vercel mô tả gói Hobby là "cho mục đích cá nhân, phi
thương mại". Quyết định kỹ thuật đã có (D-18) là: dùng Hobby tới khi có đối tác trả tiền đầu tiên, sau đó chuyển lên
Pro. Gói Pro giá 20 USD mỗi thành viên mỗi tháng, cộng phí theo mức dùng vượt phần gói đã bao gồm. *Phương án:* (A)
chuyển lên Pro trước lần thu tiền đối tác đầu tiên, đúng như D-18; (B) chuyển sớm hơn, ngay khi đối tác đầu tiên bắt
đầu dùng portal dù chưa trả tiền, như nghiên cứu S245 gợi ý vì Hobby là gói phi thương mại. Vì portal đã rời Vercel,
câu hỏi về gói Hobby nay chủ yếu liên quan tới Trip Planner, là trang bán hàng công khai. Mọi khoản chi mới cần trưởng
nhóm kỹ thuật duyệt (DM-10.7). *Đề xuất:* A. *Chi tiết:*
[`04-economics-compliance-security.md`](../audits/2026-10-20-S245-tenant-crm/research/04-economics-compliance-security.md).

## 12. Điều khoản sử dụng AI

*Hiện trạng:* Chính sách sử dụng của Anthropic có hiệu lực từ 12/11/2026 (bản đang đăng đã được đọc lại ngày
24/10/2026) và áp dụng cho các đối tác có nội dung được viết bằng Claude qua Amazon Bedrock. Phụ lục AI đầy đủ cho điều
khoản đối tác đang ở bản Draft v0.2. Từ thay đổi AA-820 trên portal, mục 3 của điều khoản portal có một bản tóm tắt
ngắn của phụ lục này (Phụ lục A.4), vẫn nằm dưới nhãn "Draft — pending legal review". Hiện chưa có đối tác thật hay đối
tác trả tiền, nên không cần gửi thông báo cho ai: mỗi đối tác chấp nhận phụ lục khi tham gia, cùng với hợp đồng đối tác.
CRM cho đại lý chưa gọi Claude; phụ lục phải nằm trong điều khoản cho đại lý trước khi CRM gọi Claude. Cần chủ doanh
nghiệp trả lời trước ngày 11/11/2026, một ngày trước khi chính sách có hiệu lực. *Phương án:* (A) áp dụng phụ lục như
bản hiện tại: bản tóm tắt trên portal đã có trước 11/11/2026, phụ lục được đính kèm mọi hợp đồng đối tác khi đối tác
tham gia, còn việc nhờ luật sư xem là tùy chủ doanh nghiệp quyết định; (B) luật sư xem phụ lục trước, và portal giữ bản
tóm tắt ở trạng thái bản nháp cho tới lúc đó; (C) áp dụng ngay như phương án A, và nhờ luật sư xem trước khi có đối tác
trả tiền đầu tiên. *Đề xuất:* A hoặc C. Vì chưa có đối tác, áp dụng ngay không tốn gì và kịp mốc 12/11/2026; phương án C
thêm một lần xem của luật sư trước khi đối tác đầu tiên trả tiền. *Chi tiết:*
[bản nháp điều khoản sử dụng AI](tenant-terms-ai-clause-draft.md): từng phần đặt ở đâu (mục 0), phụ lục (mục 2) và 14
câu hỏi cho luật sư (mục 6).

## Phụ lục A: nội dung hiện tại của bốn trang

Nội dung dưới đây được chép từ mã nguồn trang, đúng như hiển thị: A.1 và A.2 tại commit `8327bb0` (28/10/2026) của
AA-TripPlanner-Web, A.3 và A.4 tại commit `a33ccf4` (28/10/2026) của AA-Partner. Các trang portal được chuyển từ
AA-CIS-App sang AA-Partner cùng lịch sử thay đổi (AA-979); nội dung của chúng là bản ngày 20/10/2026 cộng nội dung AA-820
ở mục 3 của A.4 (24/10/2026). Mỗi trang có nhãn "Draft — pending legal review". Hai trang Trip Planner ghi phiên bản
"Draft v0.1" (20 October 2026), dù nội dung đã được thêm phần đăng nhập của khách và phần Geoapify về sau; hai trang
portal ghi "Draft v0.2" (24 October 2026) từ thay đổi AA-820. Link được ghi bằng chữ hiển thị. Các trang chỉ có bản tiếng
Anh; phần dưới đây là bản dịch để tham khảo, còn câu chữ pháp lý là bản tiếng Anh. Nếu trang thay đổi sau các commit trên,
trang đang chạy là bản đúng.

Có hai việc cần sửa nội dung trang đã biết. Mục 6 của chính sách quyền riêng tư portal vẫn ghi Vercel lưu trữ các trang
portal, dù portal nay chạy trên AWS. Hai trang Trip Planner đã đổi sau ngày 20/10/2026 nhưng vẫn ghi ngày đó.

### A.0 Các điểm cần xác nhận trên bốn trang

Mọi điểm "[to be confirmed]" trong A.1 đến A.4, kèm chủ đề trong bộ hồ sơ này có đề xuất trả lời.

| Trang, mục | Điểm cần xác nhận | Chủ đề |
|---|---|---|
| A.1 §1, A.3 §1 | Pháp nhân chịu trách nhiệm dữ liệu và địa chỉ đăng ký | 1 |
| A.2 §1, A.4 §1 | Pháp nhân vận hành | 1 |
| A.1 §4, A.3 §4 | Cơ sở pháp lý cho từng mục đích sử dụng dữ liệu | 2 |
| A.1 §6 | Danh sách đầy đủ nhà cung cấp dịch vụ, ghi trong sổ đăng ký | 4 |
| A.3 §5 | Danh sách đầy đủ nhà cung cấp AI | 4 |
| A.1 §7, A.3 §7 | Biện pháp bảo vệ khi chuyển dữ liệu ra ngoài nước của người dùng | 7 |
| A.1 §8 | Thời hạn lưu: hồ sơ khách sau khi yêu cầu hoặc đặt tour kết thúc; chuyến đi chưa gửi; tài khoản đăng nhập | 2, 5 |
| A.3 §8 | Thời hạn lưu hồ sơ đăng bài và nhật ký quản trị; dữ liệu tài khoản và nội dung sau khi tài khoản kết thúc | 2, 5 |
| A.1 §9, A.3 §9 | Thời hạn trả lời yêu cầu; quyền khiếu nại tới cơ quan bảo vệ dữ liệu | 6 |
| A.1 §11 | Tuổi tối thiểu | 2 |
| A.2 §2 | Điều kiện đặt tour | 2 |
| A.2 §7 | Giới hạn trách nhiệm, bảo đảm và quyền của người tiêu dùng | 2 |
| A.2 §8, A.4 §9 | Luật áp dụng và tòa án có thẩm quyền (A.4 mục 9 gồm cả giới hạn trách nhiệm) | 2 |
| A.3 §10 | Thỏa thuận xử lý dữ liệu giữa đối tác và Adventure Asia | 4 |
| A.4 phần mở đầu | Quan hệ giữa điều khoản này và hợp đồng đối tác đã ký | 2 |
| A.4 §3 | Duyệt bản tóm tắt điều khoản sử dụng AI (bản nháp; không còn ghi [to be confirmed]) | 12 |
| A.4 §5 | Thời hạn báo trước, chấm dứt, và nội dung được xử lý thế nào sau đó | 2 |
| A.4 §6 | Quyền sở hữu nội dung tạo ra; giấy phép dùng tour trong danh mục | 2 |
| A.4 §7 | Gói dịch vụ, phí và điều khoản thanh toán | 2 |
| A.4 §8 | Cam kết dịch vụ và giờ hỗ trợ | 8 |

### A.1 Trip Planner: Chính sách quyền riêng tư (`/privacy`)

Chính sách này giải thích Adventure Asia Trip Planner (website này) thu thập dữ liệu cá nhân nào, vì sao, ai nhận dữ
liệu đó và bạn có thể yêu cầu chúng tôi làm gì với dữ liệu đó. Chính sách chỉ áp dụng cho Trip Planner. Chính sách chung
của Adventure Asia ở adventure.asia/privacy-policy.

**1. Chúng tôi là ai.** Trip Planner do Adventure Asia vận hành. Pháp nhân chịu trách nhiệm dữ liệu của bạn (bên kiểm
soát dữ liệu) và địa chỉ đăng ký là [to be confirmed]. Mọi câu hỏi hoặc yêu cầu về quyền riêng tư, xin gửi tới
`info@adventure.asia`.

**2. Chúng tôi thu thập gì.** Bạn có thể xem tour và dựng chuyến đi mà không cần cho chúng tôi tên hay thông tin liên hệ.

- **Chuyến đi của bạn.** Điểm đến, điểm dừng, hoạt động, số ngày và số khách bạn chọn, và thứ tự các ngày. Chuyến đi được
  lưu dưới một mã khách ngẫu nhiên, không gắn với tên bạn.
- **Nội dung bạn gõ vào ô tìm kiếm của planner.** Dùng để tìm địa điểm và hoạt động phù hợp. Xin đừng gõ thông tin cá
  nhân vào ô tìm kiếm.
- **Thông tin liên hệ của bạn, chỉ khi bạn gửi chuyến đi cho tư vấn viên.** Họ tên đầy đủ, số điện thoại và/hoặc địa chỉ
  e-mail, và việc bạn có đồng ý để tư vấn viên liên hệ hay không, kèm ngày giờ bạn đồng ý.
- **Tài khoản của bạn, chỉ khi bạn đăng nhập.** Địa chỉ e-mail của bạn, được xác minh bằng một mã chúng tôi gửi qua
  e-mail (không có mật khẩu), do dịch vụ đăng nhập của chúng tôi (Amazon Cognito) lưu giữ. Bản thân planner chỉ lưu một
  mã tài khoản ngẫu nhiên và thời điểm bạn đăng nhập gần nhất, và gắn các chuyến đi bạn soạn với mã đó để bạn mở được
  chúng trên mọi thiết bị. Khi bạn đăng nhập, các chuyến đi đã soạn trên trình duyệt này trước lúc đăng nhập (và chưa
  thuộc tài khoản khác) được thêm vào tài khoản của bạn, vì vậy trên máy dùng chung, hãy đăng xuất khi dùng xong. Khi bạn
  gửi chuyến đi lúc đang đăng nhập, tư vấn viên nhận địa chỉ e-mail đăng nhập của bạn, có đánh dấu đã xác minh.
- **Dữ liệu kỹ thuật.** Các nhà cung cấp dịch vụ lưu trữ của chúng tôi xử lý địa chỉ IP, loại trình duyệt và các trang
  bạn yêu cầu để phục vụ website và giữ an toàn cho website.

**3. Cookie và bộ nhớ trình duyệt.** Chúng tôi chỉ dùng những gì planner cần để hoạt động. Chúng tôi không dùng cookie
quảng cáo hay thống kê.

- **Cookie khách** (chỉ đặt trên trang planner): một mã ngẫu nhiên chứng minh chuyến đi đã lưu là của bạn. Script trên
  trang không đọc được cookie này; cookie tồn tại tối đa 400 ngày và được gia hạn mỗi lần bạn dùng planner. Chúng tôi chỉ
  lưu bản băm một chiều của nó.
- **Cookie đăng nhập** (chỉ khi bạn đăng nhập): phiên đăng nhập đã mã hoá của bạn, để bạn giữ trạng thái đăng nhập tối đa
  30 ngày, và, trong 10 phút khi bạn nhập mã gửi qua e-mail, bước bạn đang ở. Script trên trang không đọc được các cookie
  này. Đăng xuất sẽ xoá chúng, cùng với cookie khách của trình duyệt đó.
- **Bộ nhớ trình duyệt:** các mã ngẫu nhiên của chuyến đi hiện tại, để tải lại trang vẫn khôi phục được chuyến đi, và lựa
  chọn giao diện sáng hoặc tối của bạn.

Xoá dữ liệu trình duyệt sẽ xoá các mục này; khi đó bạn bắt đầu một chuyến đi mới.

**4. Chúng tôi dùng dữ liệu của bạn thế nào.**

- Để dựng, lưu và hiển thị chuyến đi của bạn (cung cấp dịch vụ bạn yêu cầu).
- Để chuyển chuyến đi và thông tin liên hệ của bạn cho một tư vấn viên của Adventure Asia, người sẽ liên hệ bạn về chuyến
  đi đó. Chúng tôi chỉ làm việc này sau khi bạn tích ô đồng ý trên form, và chúng tôi ghi lại sự đồng ý đó kèm ngày, giờ
  và nguồn.
- Sự đồng ý của bạn áp dụng cho việc liên hệ về chuyến đi bạn đã gửi. Chúng tôi không dùng nó cho bản tin hay tiếp thị
  khác.
- Để giữ an toàn cho dịch vụ và ngăn lạm dụng.

Cơ sở pháp lý cho từng mục đích sử dụng theo luật áp dụng cho bạn là [to be confirmed].

**5. Tính năng AI.** Planner dùng mô hình AI để viết phần mô tả từng ngày của chuyến đi và để khớp nội dung tìm kiếm của
bạn với địa điểm. Các mô hình này chạy trên Amazon Bedrock (Amazon Web Services). Chúng tôi gửi cho chúng nội dung chuyến
đi (địa điểm, hoạt động, các ngày) và nội dung tìm kiếm của bạn, không bao giờ gửi tên hay thông tin liên hệ. Mọi lịch
trình đều được một tư vấn viên của Adventure Asia xem lại trước khi bạn đặt.

**6. Ai nhận dữ liệu của bạn.**

- **Tư vấn viên của Adventure Asia**, qua hệ thống đặt tour của Adventure Asia, nơi nhận các chuyến đi bạn gửi và giữ hồ
  sơ khách hàng. Tư vấn viên được báo có yêu cầu mới qua e-mail.
- **Amazon Web Services** — lưu trữ, cơ sở dữ liệu, các mô hình AI nêu trên (Amazon Bedrock), đăng nhập (Amazon Cognito)
  và các e-mail: thông báo cho tư vấn viên và mã đăng nhập (Amazon SES).
- **Vercel** — lưu trữ và phục vụ website này.
- **Mapbox** — hình bản đồ và bản đồ tương tác. Trình duyệt của bạn tải chúng từ Mapbox, nên Mapbox nhận địa chỉ IP của
  bạn và vùng bản đồ bạn xem.

Chúng tôi không bán dữ liệu cá nhân của bạn. Danh sách đầy đủ các nhà cung cấp dịch vụ sẽ được ghi trong một sổ đăng ký
[to be confirmed].

**7. Dữ liệu của bạn được lưu ở đâu.** Cơ sở dữ liệu và máy chủ của chúng tôi ở Mỹ (Amazon Web Services). Vercel và
Mapbox phục vụ website và bản đồ từ các điểm gần bạn. Biện pháp bảo vệ khi chuyển dữ liệu ra ngoài nước của bạn là [to be
confirmed].

**8. Chúng tôi giữ dữ liệu bao lâu.** Thời hạn lưu đang được xác định và là [to be confirmed]. Kế hoạch hiện tại: bản sao
thông tin liên hệ của bạn trong tin nhắn chuyển chuyến đi sang hệ thống đặt tour được xoá sau 90 ngày, và hồ sơ khách
hàng trong hệ thống đặt tour được giữ trong thời gian yêu cầu hoặc đặt tour của bạn còn hiệu lực, rồi thêm một khoảng
thời gian [to be confirmed]. Các chuyến đi chưa bao giờ được gửi [retention to be confirmed]. Tài khoản đăng nhập được giữ
trong thời gian còn được dùng và được xoá cùng liên kết tới các chuyến đi của bạn khi bạn yêu cầu [period to be
confirmed].

**9. Quyền của bạn.** Bạn có thể yêu cầu chúng tôi cho xem dữ liệu chúng tôi giữ về bạn, sửa, xoá, hoặc ngừng liên hệ bạn,
và bạn có thể rút lại sự đồng ý bất cứ lúc nào. Xin gửi tới `info@adventure.asia`. Thời hạn chúng tôi trả lời, và quyền
khiếu nại tới cơ quan bảo vệ dữ liệu của bạn, là [to be confirmed].

**10. Bảo mật.** Website dùng kết nối mã hoá (HTTPS). Cơ sở dữ liệu của chúng tôi không truy cập được từ internet, và chỉ
các hệ thống cần dùng mới được truy cập. Không có phương pháp nào an toàn tuyệt đối; nếu một sự cố rò rỉ ảnh hưởng tới dữ
liệu của bạn, chúng tôi sẽ báo cho bạn theo yêu cầu của luật.

**11. Trẻ em.** Trip Planner không dành cho trẻ em. Tuổi tối thiểu là [to be confirmed].

**12. Thay đổi chính sách này.** Chúng tôi sẽ đăng các thay đổi trên trang này kèm ngày mới. Xem thêm Điều khoản sử dụng
của chúng tôi.

### A.2 Trip Planner: Điều khoản sử dụng (`/terms`)

Các điều khoản này áp dụng khi bạn dùng Adventure Asia Trip Planner (website này). Khi dùng website, bạn chấp nhận các
điều khoản này. Nếu bạn không đồng ý, xin đừng dùng website.

**1. Trip Planner là gì.** Trip Planner là công cụ miễn phí để khám phá các tour của Adventure Asia và phác thảo ý tưởng
chuyến đi theo từng ngày. Trip Planner do Adventure Asia vận hành; pháp nhân vận hành là [to be confirmed].

**2. Kế hoạch chuyến đi không phải là đặt tour.**

- Chuyến đi bạn dựng hoặc gửi cho tư vấn viên là một yêu cầu. Không có gì được giữ chỗ hay thanh toán, và không có hợp
  đồng dịch vụ du lịch nào được lập qua website này.
- Một tư vấn viên của Adventure Asia xem chuyến đi của bạn và liên hệ bạn để xác nhận hậu cần, tình trạng chỗ và giá. Việc
  đặt tour chỉ có khi bạn đồng ý với Adventure Asia theo các điều kiện đặt tour riêng [booking conditions to be
  confirmed].
- Giá, tình trạng chỗ và lịch trình hiển thị trên website chỉ mang tính tham khảo và có thể thay đổi.

**3. Nội dung có AI hỗ trợ.** Một số phần mô tả trên website, kể cả phần mô tả từng ngày của chuyến đi, được viết với sự
hỗ trợ của AI và có ghi nhãn như vậy. Chúng có thể có sai sót. Đừng dựa vào chúng cho các quyết định về đi lại, thị thực,
sức khoẻ hay an toàn; tư vấn viên của bạn xác nhận chi tiết trước khi đặt bất cứ thứ gì.

**4. Sử dụng website.**

- Cung cấp thông tin liên hệ chính xác khi gửi chuyến đi, và chỉ thông tin của chính bạn.
- Chỉ dùng website để lên kế hoạch cho chuyến đi của chính bạn, và đúng theo luật.
- Không tìm cách truy cập chuyến đi của người khác, làm quá tải hay gây gián đoạn dịch vụ, hoặc sao chép hàng loạt nội
  dung bằng công cụ tự động.

Chúng tôi có thể hạn chế hoặc chặn truy cập vi phạm các quy định này.

**5. Nội dung và bản đồ.** Các tour, văn bản, hình ảnh và thiết kế của website thuộc về Adventure Asia hoặc các bên cấp
phép cho Adventure Asia. Bản đồ do Mapbox và những người đóng góp OpenStreetMap cung cấp theo điều khoản riêng của họ. Vị
trí các địa điểm được xác định toạ độ bằng Geoapify (geoapify.com) từ dữ liệu OpenStreetMap (© OpenStreetMap
contributors, ODbL); địa điểm nào chúng tôi chỉ xác định được gần đúng thì được hiển thị là một vùng, không phải một điểm
chính xác. Bạn được dùng website để lên kế hoạch chuyến đi cá nhân, phi thương mại.

**6. Tình trạng hoạt động và thay đổi.** Website đang được phát triển. Các tính năng có thể thay đổi, và website có lúc
không truy cập được. Chúng tôi có thể cập nhật các điều khoản này; ngày ở đầu trang cho biết phiên bản hiện hành.

**7. Trách nhiệm.** Giới hạn trách nhiệm, bảo đảm và quyền của người tiêu dùng theo luật áp dụng cho bạn là [to be
confirmed].

**8. Luật áp dụng.** Luật áp dụng và tòa án có thẩm quyền là [to be confirmed].

**9. Liên hệ.** Câu hỏi về các điều khoản này: `info@adventure.asia`. Cách chúng tôi xử lý dữ liệu cá nhân được mô tả
trong Chính sách quyền riêng tư.

### A.3 Partner Portal: Chính sách quyền riêng tư (`/privacy`)

Chính sách này giải thích Adventure Asia Partner Portal thu thập dữ liệu cá nhân nào về các doanh nghiệp đối tác và
những người dùng portal, vì sao, và ai nhận dữ liệu đó. Chính sách chung của Adventure Asia ở
adventure.asia/privacy-policy.

**1. Chúng tôi là ai.** Partner Portal do Adventure Asia vận hành. Pháp nhân chịu trách nhiệm dữ liệu của bạn (bên kiểm
soát dữ liệu) và địa chỉ đăng ký là [to be confirmed]. Câu hỏi và yêu cầu về quyền riêng tư: `info@adventure.asia`.

**2. Chúng tôi thu thập gì.**

- **Tài khoản đối tác.** Tên doanh nghiệp, gói dịch vụ và trạng thái tài khoản của bạn, và khoá API bạn dùng để đăng
  nhập. Chúng tôi kiểm tra khoá trên máy chủ; sau đó trình duyệt giữ một phiên đăng nhập.
- **Thiết lập thương hiệu và nội dung.** Giọng văn thương hiệu và các thiết lập bạn nhập, các bản viết lại tour và bài
  mạng xã hội hoặc blog được tạo cho bạn, và các chỉnh sửa của bạn.
- **Kết nối kênh.** Các thông tin bạn cung cấp để đăng bài lên kênh của chính bạn (ví dụ một trang WordPress hoặc một
  Facebook Page).
- **Bản ghi hoạt động.** Mỗi lần gọi mô hình AI (nhà cung cấp, mô hình, chi phí, thời gian, đối tác và job), mỗi lần đăng
  và gỡ bài (bài, kênh, mã bài đăng, trạng thái, thời gian, và tài khoản của bạn hay một quản trị viên Adventure Asia đã
  thực hiện), và một nhật ký quản trị ghi các thay đổi trên tài khoản đối tác.
- **Dữ liệu kỹ thuật.** Địa chỉ IP, loại trình duyệt và nhật ký yêu cầu, do các nhà cung cấp dịch vụ lưu trữ và các hệ
  thống bảo mật của chúng tôi xử lý.

**3. Cookie.** Portal chỉ dùng cookie đăng nhập, script trên trang không đọc được các cookie này. Chúng giữ phiên làm
việc của bạn và hết hạn sau 24 giờ hoặc khi bạn đăng xuất. Chúng tôi không dùng cookie quảng cáo hay thống kê.

**4. Chúng tôi dùng dữ liệu của bạn thế nào.**

- Để vận hành tài khoản của bạn và tạo nội dung bạn yêu cầu.
- Để đăng hoặc gỡ một bài trên các kênh của bạn khi bạn yêu cầu.
- Để hỗ trợ bạn, giữ an toàn cho dịch vụ, và thực thi điều khoản đối tác.
- Để đo chi phí và chất lượng dịch vụ của chính chúng tôi.

Cơ sở pháp lý cho từng mục đích sử dụng là [to be confirmed].

**5. Xử lý bằng AI.** Nội dung được tạo bởi các mô hình AI: Claude (Anthropic) qua Amazon Bedrock, và các nhà cung cấp AI
khác xem lại và chấm điểm bản nháp. Các mô hình nhận nội dung tour, thiết lập thương hiệu của bạn và hướng dẫn cho từng
bài. Chính sách của chúng tôi là không gửi dữ liệu cá nhân cho các mô hình này và không lưu dữ liệu cá nhân trong bản ghi
các lần gọi AI, vì vậy xin đừng nhập dữ liệu cá nhân về người khác vào thiết lập thương hiệu hay nội dung. Danh sách đầy
đủ các nhà cung cấp AI là [to be confirmed].

**6. Ai nhận dữ liệu của bạn.**

- **Nhân viên Adventure Asia**, để hỗ trợ và kiểm duyệt (họ có thể tạm ngưng một tài khoản hoặc gỡ một bài mà Adventure
  Asia đã đăng giúp bạn).
- **Amazon Web Services** — lưu trữ, cơ sở dữ liệu, Amazon Bedrock.
- **Vercel** — lưu trữ và phục vụ các trang của portal.
- **Các nhà cung cấp AI** như mô tả ở trên.
- **Các kênh của bạn** (ví dụ WordPress hoặc Meta), khi bạn đăng bài lên đó.

Chúng tôi không bán dữ liệu cá nhân.

**7. Dữ liệu của bạn được lưu ở đâu.** Cơ sở dữ liệu và máy chủ của chúng tôi ở Mỹ (Amazon Web Services). Biện pháp bảo
vệ khi chuyển dữ liệu ra ngoài nước của bạn là [to be confirmed].

**8. Chúng tôi giữ dữ liệu bao lâu.**

- Bản ghi các lần gọi mô hình AI: 180 ngày.
- Nhật ký bảo mật: 365 ngày.
- Hồ sơ đăng bài và nhật ký quản trị: một thời hạn sẽ được đặt trước khi chạy chính thức [to be confirmed].
- Dữ liệu tài khoản và nội dung: trong thời gian tài khoản còn hoạt động, sau đó [to be confirmed].

**9. Quyền của bạn.** Bạn có thể yêu cầu xem, sửa hoặc xoá dữ liệu cá nhân chúng tôi giữ về bạn. Xin gửi tới
`info@adventure.asia`. Thời hạn trả lời và quyền khiếu nại tới cơ quan bảo vệ dữ liệu của bạn là [to be confirmed].

**10. Dữ liệu về khách hàng của chính bạn.** Nếu bạn đưa dữ liệu cá nhân của người khác vào portal, bạn chịu trách nhiệm
bảo đảm mình có quyền làm việc đó. Thỏa thuận xử lý dữ liệu giữa bạn và Adventure Asia là [to be confirmed].

**11. Thay đổi chính sách này.** Chúng tôi sẽ đăng các thay đổi trên trang này kèm ngày mới. Xem thêm điều khoản đối tác.

### A.4 Partner Portal: Điều khoản đối tác (`/terms`)

Các điều khoản này áp dụng cho doanh nghiệp đối tác dùng Adventure Asia Partner Portal và API của portal. Chúng sẽ là một
phần, hoặc đi kèm, hợp đồng đối tác bạn ký với Adventure Asia [relationship to be confirmed].

**1. Dịch vụ.** Portal cung cấp cho bạn các tour trong danh mục của Adventure Asia được viết lại theo giọng văn thương
hiệu của bạn, các bài mạng xã hội và blog về những tour đó, và công cụ để xuất hoặc đăng chúng lên kênh của chính bạn.
Pháp nhân vận hành là [to be confirmed].

**2. Tài khoản và khoá API của bạn.**

- Giữ bí mật khoá API. Mọi hoạt động dưới khoá của bạn được coi là của bạn.
- Báo ngay cho chúng tôi qua `info@adventure.asia` nếu bạn nghĩ người khác đã biết khoá, để chúng tôi thu hồi khoá.

**3. Nội dung do AI tạo và quy định sử dụng.**

- Nội dung được tạo bằng AI và có thể có sai sót. Portal hiển thị điều này ở bước xem lại, đăng và xuất: "Nội dung này
  được tạo bằng AI. Hãy xem lại trước khi đăng; bạn chịu trách nhiệm về những gì bạn đăng." (trang hiển thị câu này bằng
  tiếng Anh).
- Nội dung được viết bằng mô hình của các nhà cung cấp bên thứ ba, trong đó có Claude của Anthropic qua Amazon Web
  Services. Bạn phải tuân theo chính sách sử dụng của họ, gồm Chính sách sử dụng của Anthropic và Chính sách sử dụng chấp
  nhận được của AWS, cũng như các điều khoản này.
- Bạn không được dùng portal hay nội dung của portal để:
  - tạo đánh giá, xếp hạng hay lời chứng thực giả, hoặc trích dẫn và câu chuyện được trình bày như của khách hàng trong
    khi họ không nói ra;
  - tạo nhân vật bịa đặt, tài khoản giả, hoặc nội dung gán cho một người thật không viết hay không duyệt nội dung đó;
  - tạo dư luận giả, hoặc mạng lưới website hay tài khoản trông như độc lập nhưng thực ra không độc lập;
  - che giấu việc tài trợ hay quan hệ thương mại, hoặc gỡ bỏ phần công bố mà luật hoặc một kênh yêu cầu;
  - gieo vào công cụ tìm kiếm hay hệ thống AI nội dung trình bày sai nguồn gốc, tác giả hoặc tính độc lập của nó;
  - gửi thư rác, hoặc đăng bài nhằm lách giới hạn đăng bài;
  - đưa thông tin sai hoặc gây hiểu lầm, nhất là về thị thực và quy định nhập cảnh, sức khoẻ, an toàn, giá hoặc tình
    trạng chỗ;
  - tư vấn về bảo hiểm, tài chính, thị thực hay các vấn đề rủi ro cao khác, trừ khi một người có chuyên môn xem lại trước
    khi gửi và người nhận được cho biết có dùng AI;
  - lách các bước kiểm tra nội dung, giới hạn hay các biện pháp bảo vệ khác của Adventure Asia.
- Nếu luật hoặc quy định của một kênh yêu cầu nội dung phải ghi nhãn do AI tạo, bạn thêm nhãn đó.
- Bạn xem lại từng bài trước khi đăng, và bạn là người đăng bài. Việc bạn yêu cầu Adventure Asia đăng một bài, trên
  portal hay qua API, xác nhận rằng bạn đã xem lại bài đó.
- Adventure Asia có thể giữ lại, viết lại hoặc từ chối tạo hay đăng nội dung vi phạm các quy định này. Việc gỡ bài và tạm
  ngưng tài khoản được nêu ở mục 4 và 5.

**4. Đăng bài lên kênh của bạn.**

- Adventure Asia chỉ đăng một bài lên kênh của bạn khi bạn yêu cầu đăng bài đó, bằng quyền truy cập bạn đã kết nối. Bài
  đăng xuất hiện dưới tên bạn.
- Có giới hạn hằng ngày về số bài Adventure Asia đăng giúp bạn.
- Bạn có thể gỡ bài của mình. Adventure Asia cũng có thể gỡ một bài mà mình đã đăng giúp bạn, ví dụ khi bài đó vi phạm các
  điều khoản này.

**5. Tạm ngưng và chấm dứt dịch vụ.** Adventure Asia có thể tạm ngưng một tài khoản, việc này dừng ngay quyền truy cập API
và việc đăng bài, ví dụ để bảo vệ dịch vụ hoặc khi các điều khoản này bị vi phạm. Thời hạn báo trước, việc chấm dứt và
nội dung của bạn được xử lý thế nào sau đó là [to be confirmed].

**6. Quyền đối với nội dung.** Ai sở hữu nội dung được tạo ra và giấy phép dùng các tour trong danh mục là [to be
confirmed].

**7. Gói dịch vụ và phí.** Gói dịch vụ, phí và điều khoản thanh toán là [to be confirmed].

**8. Tình trạng hoạt động.** Portal đang được phát triển; các tính năng có thể thay đổi và dịch vụ có lúc không truy cập
được. Cam kết dịch vụ và giờ hỗ trợ là [to be confirmed].

**9. Trách nhiệm và luật áp dụng.** Giới hạn trách nhiệm, luật áp dụng và tòa án có thẩm quyền là [to be confirmed].

**10. Liên hệ.** Câu hỏi: `info@adventure.asia`. Cách chúng tôi xử lý dữ liệu cá nhân được mô tả trong chính sách quyền
riêng tư.
