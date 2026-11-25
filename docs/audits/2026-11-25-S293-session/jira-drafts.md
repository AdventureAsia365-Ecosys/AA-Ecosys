# S293: nháp Jira gom S291 + S292 (CHƯA đăng)

Tech lead nói "duyệt hết" ~15:00 25/11, nhưng auto mode chặn việc đăng vì nháp chưa được hiện nguyên văn: chờ tech lead xem bản này rồi đăng (hoặc tắt auto mode).

Ảnh S291 ở `docs/audits/2026-11-24-S291-session/live/`, ảnh S292 ở `docs/audits/2026-11-25-S292-session/live/`.

## J1 — PR-25 (Booking)

@thule Cập nhật Booking đêm 24–25/11:

- Tab **Suppliers** của trip case: các booking nhà cung cấp sinh ra từ tour đã bán giờ ghi rõ "from the tour, day N" thay vì "extra item". Kiểm trên Dev với trip case thử TC-000040: 10/10 dòng đúng nhãn (ảnh).
- Thông báo nội bộ của nhân viên không còn kèm dữ liệu kỹ thuật về e-mail; nhắc hợp đồng sắp hết hạn được ghi theo từng lần gửi, nên nếu gửi dở giữa chừng thì lần sau chỉ gửi phần còn thiếu, không gửi lại cả loạt.
- Lịch mùa giá: các tour chưa có điểm đến không bị đọc lại mỗi lượt nữa; trang Seasons có thêm số "deferred". Khoảng kiểm lại (7 ngày) sửa được ở Pricing › Policy.

Ảnh: `s291-booking-suppliers-tab-from-tour.png`

## J2 — PR-30 (Khách sạn)

@thule Khách sạn qua nhiều DMC — ba chỉnh sửa sau đợt 24/11:

- Khi nhập lại bảng giá Excel, màn so sánh có thêm phần **Inventory**: allotment bị thu hẹp sẽ được báo rõ.
- Hợp đồng gốc để so sánh được chọn cố định, đúng hợp đồng mà file nhập nhắm tới, kể cả khi cùng DMC có hai hợp đồng cùng ngày bắt đầu.
- Sửa cách đếm phòng allotment: một dòng báo giá on request không còn giữ chỗ phòng của các dòng sau.

Ba điểm này đã kiểm bằng test tự động; chưa chạy lại một lượt nhập Excel thật trên Dev.

## J3 — PR-29 (Optional activity add-on)

@thule Add-on của AA trong báo giá CRM của đại lý: ngăn "AA add-on" giờ chỉ gợi ý những dịch vụ bán tại điểm đến của đúng ngày tour đó, giống thẻ ngày trên TripPlanner. Nếu cố thêm một add-on ở nơi khác, hệ thống từ chối và báo lý do. Đã lên Dev 25/11; kiểm bằng test tự động, chưa thử tay trên một báo giá thật.

## J4 — PR-24 (TripPlanner)

@thule TripPlanner: sửa một lỗi có thể làm trang lên lịch trình không mở được khi dữ liệu add-on theo ngày trả về sai dạng. Giờ trang vẫn chạy bình thường, chỉ không hiện add-on đó. Bộ kiểm tra giao diện sau mỗi lần phát hành đã xanh lại trên Dev (25/11).

## J5 — PR-27 (Nền tảng)

@thule Trang **Ecosystem status** trong CIS admin có thêm (đã lên Dev 25/11, ảnh desktop / mobile, sáng / tối):

- Bảng **What changed**: lần phát hành, đổi cài đặt, cập nhật dữ liệu, đổi định tuyến AI, có đánh dấu trên biểu đồ.
- Người phụ trách có thể **xác nhận / tạm hoãn / tắt tiếng** một cảnh báo kèm lý do, có ghi lại ai làm lúc nào. Chủ doanh nghiệp chỉ xem, không có nút.
- Nhãn "as of" cho biết dữ liệu mới tới đâu, dự báo còn bao nhiêu ngày tới giới hạn dung lượng và hạn mức AI, cảnh báo chi phí AI tăng bất thường, lưu các góc nhìn hay dùng.
- Nút **Actions** trên mỗi cảnh báo mở danh sách việc nên làm, xếp theo rủi ro, có cách quay lại. Chưa dùng AI, không tự chạy việc gì.

Ngoài ra, nếu bước kiểm tra sau phát hành báo đỏ, CIS admin, Booking admin, CRM web và TripPlanner web giờ tự quay về bản trước và mở ghi chú lỗi.

Ảnh: `s291-aa1141-status-1440-light.png`, `s291-aa1141-status-1440-dark.png`, `s291-aa1141-status-390-light.png`, `s291-aa1154-status-actions-drawer.png`

## J6 — PR-27 (Nền tảng): trang Ecosystem status, phần 2

@thule Trang **Ecosystem status** trong CIS admin, phần 2 (đã lên Dev 25/11, ảnh desktop / mobile, sáng / tối):

- **Mục tiêu dịch vụ (SLO)** cho 4 app: tỉ lệ yêu cầu thành công, phần "ngân sách lỗi" còn lại trong tháng, và cảnh báo
  sớm khi lỗi tăng nhanh. Đã thử bằng một lượt tạo lỗi giả có kiểm soát trên Dev: cảnh báo bật đúng.
- **Sự cố**: mở một hồ sơ sự cố, ghi diễn biến, đóng lại kèm nguyên nhân.
- **Theo đại lý**: xem nhanh tình trạng từng đại lý.
- **Kiểm từ bên ngoài**: 8 địa chỉ công khai (trang đăng nhập, API, web các app) được kiểm DNS, chứng chỉ và tình trạng
  từ ngoài hệ thống. <!-- CHỈ GIỮ CÂU NÀY khi lane e S293 đã cho lịch kiểm chạy đều; S293 thấy GitHub bỏ lượt chạy theo lịch -->

Ảnh: `aa1142-slo-desktop-light.png`, `aa1142-incidents-desktop-light.png`, `aa1142-agencies-desktop-light.png`,
`aa1142-external-desktop-light.png`, `aa1142-slo-mobile-light.png`

Câu → bằng chứng: SLO + burn drill (300×503 → cảnh báo nhanh bật, S292 log); 14 section 200; external 8/8 (một lượt
dispatch tay, S292).

## J7 — PR-27 (Nền tảng): trợ lý vận hành trong CIS admin

@thule Trên trang Ecosystem status, mỗi cảnh báo có nút **Analyse**: hệ thống xếp các việc nên làm theo rủi ro, giải
thích bằng lời thường, có cách quay lại và ai duyệt. Trợ lý chỉ đề xuất, không tự chạy việc gì. Có thêm ô tra cứu "đã
thay đổi gì trong 1 giờ qua". Đã lên Dev 25/11. Chủ doanh nghiệp xem được phần tóm tắt, không có nút thao tác.

Ảnh: `aa1154-drawer-desktop-light.png`, `aa1154-lookup-desktop-light-panel.png`, `aa1154-drawer-mobile-light.png`

Câu → bằng chứng: Analyse trên cảnh báo errors-cis trả 2 thẻ (S292 `evidence/aa1154-a1-analyse.txt`); phiên chỉ xem
không gửi POST nào.

## J8 — PR-29 (Optional activity add-on): điểm ngủ đêm theo ngày tour

@thule Mỗi ngày tour trong catalog giờ ghi rõ **điểm ngủ đêm**. CRM của đại lý đã nhận trường này qua lượt đồng bộ đêm
25/11, nên gợi ý add-on theo ngày bám đúng nơi khách ở tối đó. Kiểm trên Dev: 50 tour / 428 ngày đều có trường này; ở
CRM, 200/200 tour tải mới đã có trường (phần còn lại tải dần theo lịch).

Câu → bằng chứng: S292 `evidence/aa1152-overnight-cis.txt`, `aa1152-overnight-crm.json`.

## J9 — PR-22 (CIS nội dung): chất lượng blog đại lý lần viết đầu

@thule Blog viết cho đại lý: tỉ lệ bài **đạt ngay lần viết đầu** (không cần sửa) tăng từ 8 % lên 42 % trên bộ mẫu
12 bài, số lỗi mỗi bài không tăng. Còn bước người đọc lại 10 bài trước khi coi là xong.

Câu → bằng chứng: S292 `evidence/aa1169-w5-t9-r2-report.txt` (yield 0,417, lỗi/blog 1,58 vs 5,0).
