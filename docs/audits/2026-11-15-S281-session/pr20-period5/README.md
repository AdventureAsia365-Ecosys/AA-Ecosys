# PR-20 — Báo cáo nền tảng kỳ 5 (10–16/11/2026): đã đăng comment 10661 (15/11, sau khi tech lead duyệt "Đăng")

Vị trí: comment trên PR-20 (như kỳ 3, kỳ 4). Không ảnh (chi tiết và ảnh đã nằm ở comment từng epic trong tuần).
Số đo: Dev, 15/11/2026 khoảng 19:40 +07, bằng đúng các script của kỳ 4 (chạy chỉ đọc trong container CIS).

---

@thule Báo cáo nền tảng kỳ 5 (10–16/11/2026). Mọi số đo trên Dev với dữ liệu thử, còn thay đổi; số đo tối 15/11. Chi tiết và ảnh ở các comment trong tuần trên PR-22 đến PR-27.

**Tóm tắt tuần**

- Diễn tập pilot trọn hành trình qua 5 app với một đại lý thử nghiệm, rồi kết thúc hợp tác và xoá dữ liệu của đại lý đúng quy trình.
- Trang Cài đặt nền tảng thành nơi duy nhất chỉnh các ngưỡng, giới hạn và trần chi phí của cả 4 app, không cần sửa code.
- Dữ liệu nhu cầu tìm kiếm làm mới cho 6 thị trường: dòng xếp hạng địa điểm có số lượt tìm tăng từ 4–19 % lên 74–76 %. Đây là rủi ro lớn nhất của kỳ 4.
- Booking và CRM đủ các bước giá, ngày khởi hành, vận hành chuyến, thu tiền (chế độ thử). TripPlanner chạy được trên tên miền riêng của đại lý.

| App | Đã xong trong kỳ | Tiếp theo |
|---|---|---|
| CIS (PR-22) | Trang Cài đặt nền tảng: ngưỡng, giới hạn, trần chi phí của CIS, Booking, CRM, TripPlanner chỉnh ngay trên trang, có giải thích Anh/Việt, người duyệt, lịch sử, đặt riêng được cho một đại lý; đổi có hiệu lực trong khoảng 1 phút; 0 thông số bị cấu hình máy chủ ghi đè (15/11). Viết lại tour AA: số ngày, tiêu đề ngày, bữa ăn, nơi ngủ dựng thẳng từ file nguồn, AI chỉ viết phần văn (thử 3/3 đạt, 0 lỗi so với nguồn); mọi tour đang bán dùng bộ viết mới; 48 tour có cưỡi voi tạm rút khỏi danh sách bán, chờ duyệt (11/11). Chủ đề đủ chuẩn Blog ở thị trường Mỹ 391 → 1.593 sau khi làm mới dữ liệu tìm kiếm. Bộ đáp án đo chất lượng bước tự kiểm dữ kiện đủ 1.018 câu. Bài blog ngắn của đại lý: bước viết bổ sung đã làm lại và đang dùng cho đại lý thử. Ba báo cáo mới trong Reports (chi phí AI từng đại lý so với trần gói, công nợ đại lý theo tuổi nợ, tóm tắt booking tuần); bản đồ sản phẩm 117 tính năng, 37 liên kết giữa các app; trang Docs 169 trang trong 23 nhóm | Đo xong độ chính xác của bước tự kiểm dữ kiện trong bài, rồi mới quyết siết hay nới việc giữ bài; kiểm lần tự chạy đầu của hai báo cáo tuần (16/11); thêm báo cáo vận hành CRM |
| App cho đại lý, Content studio (PR-23) | Khi AA ngừng bán một tour, hệ thống không tự sửa website của đại lý: đại lý nhận chuông và email kèm danh sách bài WordPress, tự bấm "Move to draft"; tour bán lại thì bấm "Put back online" cho từng bài; bài Facebook không bị sửa; đã chạy trọn vòng trên site WordPress thử (10/11). Trang Bài viết giải thích bằng lời thường vì sao một tour chưa có chủ đề blog (4 đại lý thử: 44/49 tour có chủ đề); danh sách chủ đề lập trong khoảng 12 giây, trước đây 13–15 phút. Bảng nội dung chỉ hiện nội dung của chính đại lý; bài đang bị giữ không đăng được nếu chủ tài khoản chưa xác nhận. Điều khoản và Quyền riêng tư bản nháp v0.6 (Anh/Việt), vẫn ghi chờ luật sư xem | Kịch bản diễn tập khi đại lý hết ngân sách AI |
| TripPlanner (PR-24) | Chạy trên tên miền riêng của đại lý (ví dụ trip.&lt;tên miền đại lý&gt;): nhân viên AA thêm tên miền trong hồ sơ đại lý, hệ thống hiện 2 bản ghi DNS cho đại lý tạo rồi tự xin chứng chỉ HTTPS; thử thật 15/11 với một tên miền thử: trang HTTPS mang tên đại lý, gỡ tên miền thì về đường dẫn chung. Trang lên lịch trình mới: ảnh và biểu tượng từng điểm dừng, kéo thả (cả trên điện thoại), chia sẻ, in, tải lịch .ics; "Plan with chat" chỉ dùng tour và địa điểm của AA, trần AI 2 USD/tháng. Trên điện thoại, thời gian hiện nội dung chính 4,9 → 2,6 giây. Lịch trình của từng đại lý tách riêng trong cơ sở dữ liệu (kiểm mỗi đêm 99/99). Trang của đại lý chỉ hiện tour đại lý đã chọn (đại lý thử: 11 tour); trang tour AA không còn hiện thương hiệu đại lý | Kịch bản khi đại lý hết ngân sách AI; đầu tháng 12 đọc lại chi phí chạy TripPlanner từ hoá đơn tháng 11 |
| Booking (PR-25) | Bảng giá theo phiên bản, có lịch mùa và ngày lễ; phiên bản mới chỉ có hiệu lực khi người thứ hai duyệt. Trang Thiết lập giá (892 tour kèm tình trạng sẵn sàng bán) và trang Chính sách giá (20 thông số, người thứ hai duyệt, có lịch sử). Định giá trọn vòng ngày 14/11 với dữ liệu giả lập: 4/4 tour nhận gợi ý dịch vụ từ lịch trình CIS, nhập giá bằng Excel, giá "Từ $X" hiện đúng trên TripPlanner và Content studio. Lịch ngày khởi hành theo tháng: tỷ lệ lấp chỗ, chỗ giữ cho đại lý, ngày có nguy cơ không đủ khách, số khách tối thiểu, ngày chốt bán. Vận hành booking của đại lý: nhân viên AA nhập thay đại lý, voucher không có tên khách và giá, danh sách đoàn, huỷ một phần, giá trẻ em và phụ thu (phần ghi dữ liệu chưa thử thật trên giao diện). Chi phí và lãi theo booking, ngày khởi hành, đại lý | Nhập giá nhà cung cấp và ngày khởi hành thật cho 10–20 tour ưu tiên; lần tự chạy đầu của báo cáo công nợ đại lý (16/11) |
| CRM (PR-26) | Giá theo loại khách và theo mùa, lịch thu tiền nhiều đợt (mẫu 30/40/30), bảng phí huỷ gợi ý, hộp huỷ tính sẵn tiền hoàn. Lãi lỗ từng chuyến, hoá đơn nhà cung cấp, báo cáo lãi (vai trò trợ lý không thấy tiền lời). Cộng tác viên và hoa hồng; nút "Book now" kèm đặt cọc VNPay bằng tài khoản của đại lý (chế độ thử, mặc định tắt). Điều hành chuyến: danh sách khởi hành và khách, voucher, PDF xác nhận, danh sách phòng, kiểm hạn hộ chiếu, theo dõi visa. Khi AA huỷ một ngày khởi hành, CRM mở hướng dẫn trên từng chuyến bị ảnh hưởng (thử trọn vòng đạt 13/11). Dòng tour AA hiện trên cổng của khách; cờ khi AA ngừng bán tour. AI hỗ trợ nhân viên (soạn nháp trả lời, đọc thư xác nhận nhà cung cấp, gợi ý tour AA), mỗi đại lý tự bật, mặc định tắt. Thoả thuận đã ký tải về thành PDF có chữ ký số; mẫu tin "Booking confirmed" | Báo cáo vận hành CRM vào bộ báo cáo chung; trước pilot thật, chạy trang web CRM bằng 2 bản để không gián đoạn khi cập nhật |
| Nền tảng (PR-27) | Xoá dữ liệu khi đại lý ngừng hợp tác đã chạy thật trên cả 4 app với đại lý giả lập (14 và 15/11): mỗi lượt chạy thử trước, có người duyệt, có sao lưu; kiểm lại độc lập không còn dữ liệu cá nhân; khôi phục thử dữ liệu TripPlanner của một đại lý: 42/42 dòng khớp. Rà bảo mật trước khi nhận dữ liệu cá nhân thật: ở Booking mỗi đại lý chỉ đọc được hồ sơ của mình (kiểm 9/9); CRM từ chối thông báo thanh toán VNPay sai chữ ký. AA Academy (trang học cho đội ngũ AA): bài học, bài kiểm tra, chứng chỉ, trang kiểm chứng chỉ công khai (thử trọn vòng 6/6). Trang "Infra limits" giải thích từng giới hạn hạ tầng | Dữ liệu đại lý của buổi diễn tập xoá theo lịch, sớm nhất 14/12/2026 (CRM 12/02/2027) |

**Diễn tập pilot (13–15/11)** — chi tiết ở comment 14/11 và 15/11 trên PR-20:

- Trọn hành trình qua 5 app trên một đại lý thử nghiệm: tạo đại lý, bài viết, khách lập kế hoạch trên TripPlanner, yêu cầu vào CRM, báo giá, đặt cọc, AA xác nhận, đặt dịch vụ nhà cung cấp, cổng của khách, kế toán hai người duyệt.
- Các bước còn lại (đặt tour online, nhập giá, ngân sách AI, bật/tắt chế độ thí điểm) đạt ngày 14–15/11.
- AA ngừng bán rồi bán lại một tour, qua 4 app: đại lý được báo, trang tour công khai đổi trạng thái, CRM gắn rồi tự gỡ cờ (chậm nhất khoảng 2 giờ).
- 40 video (34 ngày 13/11, 6 ngày 14–15/11). Kết thúc: đại lý thử đã ngừng hợp tác đúng quy trình.

**Nội dung tour** (đo 15/11, so với kỳ 4 đo 09/11):

| Bước | Kỳ 4 | Kỳ 5 |
|---|---|---|
| Tour thô đang bán (14 nước) | 917 | 917 |
| Tour Master đang phục vụ | 892 (97 %) | 844 (92 %); 48 tour có cưỡi voi tạm rút, chờ duyệt |
| Có tuyến để gợi ý trên bản đồ | 699 | 650 (giảm cùng 48 tour tạm rút) |
| Dòng xếp hạng địa điểm có số lượt tìm | 4–19 % tuỳ thị trường | 74–76 % ở cả 6 thị trường |
| Tour đã viết lại cho đại lý thử | 28 tour, 93 bản, 9 đại lý thử | 38 tour, 138 bản, 10 đại lý thử |
| Bài viết cho đại lý thử | 405 bài; 6 bài từng đăng | 469 bài; 11 bài từng đăng lên kênh của đại lý thử (chưa có đại lý thật) |

**Chi phí AI và dữ liệu tìm kiếm** (theo sổ ghi từng lượt gọi; số Dev, chưa ổn định):

| Tháng | AI (USD) | DataForSEO (USD) |
|---|---|---|
| 9 | 41,69 | 51,68 |
| 10 | 269,34 | 19,30 |
| 11 (tới 15/11) | 35,48 | 10,55 |

- Riêng tuần 10–15/11: AI 18,43 USD.
- DataForSEO tháng 11 gần như toàn bộ là đợt làm mới dữ liệu tìm kiếm cho 6 thị trường ngày 09–10/11 (10,04 USD); từ đó tới nay không mua thêm.

**Kế hoạch tuần tới (17–23/11):**

| Việc | Cuối tuần muốn có |
|---|---|
| Chất lượng bài viết: đo xong độ chính xác của bước tự kiểm dữ kiện trong bài (lấy thêm mẫu cho đủ, rồi chạy lượt đo chính thức) | Biết bước kiểm bắt đúng bao nhiêu và báo nhầm bao nhiêu; từ đó quyết giữ bài ít hơn hay nhiều hơn |
| Chạy thử có trả phí trên một bộ mẫu nhỏ cố định cho các bộ viết (tour AA, tour cho đại lý, bài viết), có trần chi phí | Số đo trước/sau để chọn cách viết, không chạy cả catalogue |
| Báo cáo: kiểm lần tự chạy đầu của hai báo cáo tuần (16/11); thêm báo cáo vận hành CRM | Báo cáo tuần chạy đúng lịch; báo cáo CRM có trong mục Reports |
| TripPlanner trên tên miền riêng: làm nốt phần hạ tầng còn lại | Đóng tính năng, đại lý dùng được khi cần |
| Diễn tập hai tình huống còn thiếu: Content studio và TripPlanner khi đại lý hết ngân sách AI | Có video và kết quả đạt/không đạt |
| Từ 19/11, chuẩn bị bước kiểm bài mới: bài thiếu độ dài, lệch phạm vi tour hoặc lệch giọng thương hiệu được sửa một lần thay vì bị giữ | Chạy thử trên mẫu nhỏ trước khi bật |
| CRM phần mua thêm (tìm kiếm và thư viện, chiến dịch email, kết nối Microsoft 365 và lịch): bắt đầu khi các việc trên ổn | Phần lớn thời gian vẫn dành cho nội dung |

Phía dữ liệu của AA, làm song song khi tiện: giá nhà cung cấp và ngày khởi hành của 10–20 tour ưu tiên; sửa số ngày tour "Kayak and Hike Wild Thailand" trong file Excel gốc.

Mốc ngày: 16/11 hai báo cáo tuần tự chạy lần đầu; từ 28/11 xoá hẳn dữ liệu khách lẻ cũ trong Booking; đầu tháng 12 đối chiếu chi phí tháng 11 với hoá đơn.

**Rủi ro:**

- Tài khoản AWS dự kiến cho AI vẫn bị AWS chặn một số model. AI viết nội dung chạy qua đường thay thế, không gián đoạn.
- Giá thật còn rất ít: đo 10/11, 2/892 tour đủ điều kiện bán và 4 ngày khởi hành mở. Pilot thật cần giá nhà cung cấp và ngày khởi hành thật của các tour ưu tiên.
- Catalogue thiếu dữ liệu nguồn, cần người bổ sung: 730 tour chưa có ảnh bìa, 281 tour không có giá tham chiếu trong file nguồn (đo 10/11). Tour "Kayak and Hike Wild Thailand" ghi 9 ngày nhưng lịch trình có 10 ngày; hệ thống đã dùng 10 ngày, file Excel gốc nên sửa theo.
- Còn chưa thử thật: VNPay bằng tài khoản thật của đại lý, PDF ký số với chứng thư thật, phần ghi dữ liệu vận hành Booking trên giao diện, Content studio và TripPlanner khi đại lý hết ngân sách AI.
- Bài blog của đại lý vẫn có bài bị giữ để kiểm (1/2 bài thử ngày 15/11). Đại lý vẫn nhận bài; bước tự kiểm dữ kiện đang được đo.

**Đang chạy theo phương án đề xuất** (đổi được trên trang quản trị): bảng 10 giá trị mặc định cho CRM và Booking (comment 10/11 trên PR-26). Điều khoản phí theo ngày khởi hành trong Booking đang ở dạng nháp, chưa hiện cho đại lý.

---

## Câu → bằng chứng

| Câu | Bằng chứng |
|---|---|
| Mọi mục "Đã xong" theo app | Comment đã đăng trong kỳ: PR-22 10629, 10630, 10631, 10640, 10641, 10649, 10655, 10657; PR-23 10633, 10638, 10647; PR-24 10639, 10642, 10648; PR-25 10632, 10643, 10645, 10650, 10653; PR-26 10635–10637, 10644, 10646, 10651, 10654, 10658; PR-27 10656, 10659. Rà chéo bởi agent kiểm (workflow S281 pr20-period5-gather) |
| Chủ đề 12 giây, trước 13–15 phút | Log S278 mục verify: 12,3 s / 0 lượt chấm, trước 756–894 s (chưa báo trên Jira) |
| Trang đại lý chỉ hiện 11 tour | `docs/linear-export/tripplanner-aa-booking/AA-1094.md`, comment 13/11 (chưa báo trên Jira) |
| CRM khi AA huỷ ngày khởi hành: trọn vòng đạt | `docs/linear-export/partner-crm-aa-partner/AA-1070.md`, comment 13/11 (chưa báo trên Jira) |
| Rà bảo mật 9/9, VNPay sai chữ ký | `docs/linear-export/data-platform-schema-ops-scale/AA-1092.md` (chưa báo trên Jira) |
| Diễn tập pilot, 40 video | PR-20 10652 (14/11), 10660 (15/11) |
| 917 / 844 + 48 / 650 / 38-138-10 / 469 / 11 | `system_funnel.out` 15/11 12:39Z (script kỳ 4 `.tmp-session/S273/picture/`, đầu ra không đưa vào repo): `live_active_source=917`, `by_master_status.active=844`, `inactive=48` (`policy_hold`, IN 37, TH 6, NP 4, LA 1), `routes.tours_with_route=650`, ranked tours US 883 → 835, `s09_t2 totals` 38/138/10, `piece_totals.rows=469`, `publish_totals.pieces=11` (3 tenants) |
| 48 tour cưỡi voi tạm rút 11/11 | `docs/audits/2026-11-11-S277-s1-master-audit/README.md` (Active Masters 892 → 844) |
| 74–76 % | `demand_cov.out` 15/11: positive / rows = US 75,7, UK 75,5, AU 75,3, DE 74,3, FR 74,0, NL 73,6 %; kỳ 4: US 3.090/16.203 = 19,1 %, DE 709/16.203 = 4,4 % |
| Chi phí theo tháng | `system_funnel_stats.out` 15/11: llm 09 41,69; 10 269,34; 11 35,39 + 0,09; dfs 09 51,684; 10 19,298; 11 10,548 |
| AI tuần 18,43 | `week_costs.out`: tổng theo nhóm bước từ 09/11 17:00Z (= 10/11 00:00 +07) |
| DFS 10,04 ngày 09–10/11 | `week_costs.out` dfs 11-09: 6,36 + 3,68; log S274: US/UK/AU 2,58, lượt R1 đầu lỗi (giữ dữ liệu), R2 DE 0,96 / FR 0,96 / NL |
| 2/892 tour đủ điều kiện bán, 4 ngày khởi hành | PR-25 10632 (đo 10/11), chưa đo lại |
| 730 ảnh bìa, 281 giá tham chiếu, Kayak 9→10 ngày | PR-22 10630, 10641 |
| Bảng 10 giá trị mặc định | PR-26 10636; backlog mục "Waiting after S275" chưa ghi nhận trả lời |
| Điều khoản phí ngày khởi hành dạng nháp | PR-25 10643; log S277 mục Còn lại |

Không đưa vào (luật Jira): chuyển AI sang tài khoản AWS khác, gộp thanh toán / credit, thứ tự gọi model (quyết định hạ tầng
của tech lead); GuardDuty; lỗi nội bộ đã tự xử lý; go-live (quyết định 12/11).
