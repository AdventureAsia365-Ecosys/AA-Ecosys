# S276 — nháp Jira (CHƯA ĐĂNG, chờ tech lead duyệt)

Phiên 10/11/2026 trên Dev. Mỗi nháp: issue đích, vì sao chọn, chỗ đăng, nội dung đăng nguyên văn (khi đăng: dạng HTML,
`@thule` đổi thành mention node như skill `aa-jira-update`, danh sách đổi sang `<ul>`), ảnh đề xuất, bảng câu → bằng
chứng. Không có nháp nào đổi trạng thái hay tạo issue Jira.

## Rà Jira trước khi soạn (đọc 10/11, sau 16:35 giờ VN)

- Không issue nào trong PR / KAN / CON được cập nhật sau đợt đăng S275 (JQL `updated >= "2026-11-10 16:35"` trả 0):
  đợt đăng S275 là cập nhật cuối, không có comment mới của chị Thư cần trả lời.
- Comment gần nhất đã đọc:
  - **PR-26** (CRM): 10636 bảng chọn giá trị mặc định (câu 3: bảng phí huỷ mẫu, câu 4: giảm giá 10%), 10635 phân tích
    Odoo + gói giá đầu tiên ("Tiếp theo trong CRM: lãi lỗ từng chuyến; trang Đặt với AA…"), 10624, 10621.
  - **PR-23** (Content studio): 10633 "Put back online" + điều khoản v0.6 (10/11), 10626 nhãn AI, 10616 (06/11: "chuyển
    bài WordPress về nháp sau 7 ngày chưa thử thật").
  - **PR-24** (TripPlanner): 10627 (08/11, lead vào CRM của đại lý), 10614, 10600, 10565.
  - **PR-22** (CIS): 10631 chất lượng viết, 10630 catalogue, 10629 DataForSEO (cả ba 10/11), 10622 (09/11: lý do hàng
    đầu của bài blog dưới ngưỡng là câu kêu gọi hành động, 63/151 bài).
  - **PR-25** (Booking): 10632 (10/11), 10628. Phiên này không có việc Booking riêng → không soạn.
  - **PR-20**: 10625 = **báo cáo kỳ 4 (03–09/11) ĐÃ ĐĂNG** 09/11 06:35. Kỳ 5 (10–16/11) chưa hết kỳ → không soạn.
- Story con dưới các epic (PR-11, PR-12, PR-13, PR-17, PR-18, PR-19, …): không story nào khớp riêng việc hôm nay
  (lịch thu tiền, phí huỷ, lãi lỗ, bài về tour ngừng bán, tách dữ liệu TripPlanner, phần cố định của tour AA). PR-19
  (CRM) không có comment từ 22/10; các báo cáo CRM vẫn đăng ở epic PR-26 như S275 → giữ chỗ đăng ở epic.
- Không lặp lại: "Put back online" (đã báo 10633, nháp PR-23 dưới đây chỉ nhắc một dòng); giá theo loại khách và giảm
  giá cần chủ duyệt (đã báo 10635).

---

## Nháp 1 — PR-26 "CRM cho đại lý"

Vì sao: comment 10635 hứa "Tiếp theo trong CRM: lãi lỗ từng chuyến; trang Đặt với AA"; hôm nay hai gói đó và gói thanh
toán / huỷ đã lên Dev và đã kiểm bằng trình duyệt. Bảng phí huỷ gợi ý liên quan tới câu 3 trong bảng chọn 10636.

Đăng ở: comment mới trên PR-26.

> @thule Cập nhật CRM cho đại lý ngày 10/11 (Dev, đại lý thử Sen Vàng, dữ liệu thử):
>
> **Thu tiền và huỷ chuyến**
>
> - **Lịch thu tiền nhiều đợt:** mẫu mặc định 30% khi khách chấp nhận đề xuất, 40% trước ngày khởi hành 60 ngày, phần còn lại trước 30 ngày. Mỗi đại lý sửa mẫu này trong Settings, và sửa riêng trên từng đề xuất (thêm hoặc bớt đợt, đổi % và ngày hạn).
> - **Nhắc khách trả tiền:** hai mẫu tự động, nhắc trước hạn 7 ngày và nhắc khi quá hạn 3 ngày, gửi email từ hộp thư của đại lý, mỗi khoản tối đa một lần nhắc mỗi 3 ngày. Mẫu được thêm ở trạng thái tạm dừng: chủ đại lý đọc nội dung rồi mới bật. Khi chưa bật, hệ thống không gửi gì cho khách.
> - **Chính sách huỷ theo số ngày trước khởi hành:** đại lý lập bảng phí huỷ trong Settings, bắt đầu từ bảng gợi ý của Adventure Asia, đúng phương án đề xuất ở câu 3 của bảng chọn hôm trước: từ 31 ngày trở lên 0%, 15–30 ngày 25%, 8–14 ngày 50%, dưới 8 ngày 100%; mỗi đại lý sửa được. Bảng phí được chốt vào đề xuất khi khách chấp nhận.
> - **Hộp huỷ chuyến tính sẵn:** phí huỷ theo chính sách, số tiền khách đã trả, tiền hoàn cho khách, và phí huỷ Adventure Asia thu đại lý. Khi phí thu khách thấp hơn phí Adventure Asia thu, hộp hiện cảnh báo đỏ. Đã thử trên một chuyến thử (chỉ xem trước, không huỷ thật): chuyến chưa gắn chính sách nên phí thu khách là 0, phí Adventure Asia 79,27 USD, cảnh báo hiện đúng. Chưa thử: phí tính theo một chính sách thật, vì chưa có chuyến thử nào gắn chính sách.
>
> **Lãi lỗ và công nợ**
>
> - **Lãi lỗ từng chuyến:** thẻ Money trên mỗi chuyến hiện doanh thu, chi phí Adventure Asia, chi phí nhà cung cấp riêng của đại lý, lời, % lời và lời mỗi khách. Ví dụ chuyến thử: doanh thu 540 USD, chi phí Adventure Asia 158,54 USD, lời 381,46 USD (70,64%), 190,73 USD mỗi khách.
> - **Trang "Bookings with AA":** các booking đại lý đặt với Adventure Asia, hoá đơn Adventure Asia gửi đại lý, ô báo booking lệch giá so với báo giá và hoá đơn Adventure Asia quá hạn.
> - **Hoá đơn nhà cung cấp riêng của đại lý** ghi theo từng chuyến; **chi phí chung của đoàn** (các chuyến cùng mã đoàn chia chi phí chung theo đầu khách).
> - **Báo cáo lãi** theo tháng đi, nhân viên phụ trách, nguồn khách, loại sản phẩm (tour Adventure Asia hay dịch vụ riêng), tải được CSV.
> - **Ô "hôm nay" trên trang chủ:** đề xuất đang mở, tiền cọc đến hạn trong tuần, khoản quá hạn, chuyến sắp đi còn thiếu hộ chiếu, hoá đơn Adventure Asia quá hạn.
> - **Quyền xem:** nhân viên vai trò trợ lý không thấy số tiền lời.
>
> Đã kiểm bằng trình duyệt trên Dev ngày 10/11, đăng nhập lần lượt bằng chủ đại lý, nhân viên bán hàng và trợ lý của đại lý thử.
>
> Ảnh theo thứ tự: (1) lịch thu tiền trên đề xuất; (2) bảng phí huỷ gợi ý trong Settings; (3) hộp huỷ chuyến với cảnh báo phí thấp hơn phí Adventure Asia; (4) thẻ Money của chuyến thử.

Ảnh đề xuất (4 ảnh, đổi tên không dấu khi tải lên):

| Thứ tự | File | Tên khi tải lên |
|---|---|---|
| 1 | `ui-verify/01c-builder-instalments-1440-light.png` | `crm-lich-thu-tien.png` |
| 2 | `ui-verify/01b-settings-cancellation-policy-1440-light.png` | `crm-bang-phi-huy.png` |
| 3 | `ui-verify/01d-trip-cancel-dialog-preview-1440-light.png` | `crm-hop-huy-chuyen.png` |
| 4 | `ui-verify/02a-trip-money-card-1440-light.png` | `crm-lai-lo-chuyen.png` |

| Câu | Bằng chứng |
|---|---|
| Lịch 30 / 40 trước 60 ngày / phần còn lại trước 30 ngày; sửa ở Settings và trên đề xuất | AA-Partner #261 (`6dd244de`, mẫu mặc định `deposit 30 / instalment 40 before_start 60`); ảnh `01a-settings-payments-schedule`, `01c-builder-instalments` |
| Nhắc trước 7 ngày, quá hạn 3 ngày, tối đa 1 lần / 3 ngày, thêm ở trạng thái tạm dừng | ảnh `01e-automations-payment-reminders` (chữ trên trang: "Added paused: read the message, then switch it on. Nothing is sent to travellers until you do.") |
| Bảng gợi ý 10 / 25 / 50 / 100 theo mốc 31 / 15 / 8 / 0 ngày | `DEFAULT_TIERS = ((31, "10"), (15, "25"), (8, "50"), (0, "100"))` trong #261; ảnh `01b-settings-cancellation-policy` |
| "phương án đề xuất ở câu 3, thêm mức 10%" | comment 10636 câu 3A: ≤30 ngày 25%, ≤14 ngày 50%, ≤7 ngày 100% (các mốc trùng; bản code thêm 10% từ 31 ngày) |
| Chốt vào đề xuất khi khách chấp nhận | chữ trên trang `01b`: "The client accepts it with the proposal"; migration crm-050 `proposal.cancellation_policy_id` niêm phong sau bản nháp |
| Hộp huỷ: 0 USD, 79,27 USD, cảnh báo; chỉ xem trước | ảnh `01d-trip-cancel-dialog-preview` (phiên điều phối: không bấm huỷ) |
| Chưa thử phí theo chính sách thật | phiên điều phối: chưa chuyến thử nào gắn chính sách |
| Thẻ Money: 540 / 158,54 / 381,46 / 70,64% / 190,73 | ảnh `02a-trip-money-card` |
| Bookings with AA, hoá đơn NCC, chi phí đoàn, báo cáo lãi, ô hôm nay | AA-Partner #264 (`4a9ce7ba`, CONTEXT: profit cube theo `travel_month` / `owner_member` / `lead_source` / `product`, CSV; agenda tiles); ảnh `02b`, `02c`, `02d`, `02e` |
| Trợ lý không thấy số tiền lời | ảnh `02f/02g/02h/02i-assistant-*` so với `*-agent-*` |
| Kiểm bằng trình duyệt, 3 vai trò | thư mục `ui-verify/` (chủ, agent, assistant; live check PASS trên máy tính). Một lỗi bố cục trên điện thoại đã sửa ngay sau đó, không nêu trong comment (lỗi đã tự xử lý) |

Không đưa vào comment: dòng "cộng tác viên" trong báo cáo lãi (CONTEXT ghi chiều `sales_partner` hiện chưa có dữ liệu
vì hoa hồng cộng tác viên chưa làm).

---

## Nháp 2 — PR-23 "Portal tenant — Cổng cho đối tác"

Vì sao: comment 10616 (06/11) báo luật cũ "tự chuyển bài WordPress về nháp sau 7 ngày"; hôm nay luật đổi, chị cần biết
hệ thống không còn tự sửa website của đại lý. Tiếp comment 10633 ("Put back online", chưa thử trọn vòng).

Đăng ở: comment mới trên PR-23.

> @thule Thay đổi trong Content studio ngày 10/11 (Dev): khi Adventure Asia ngừng bán một tour, hệ thống không còn tự sửa website của đại lý.
>
> - **Trước đây:** bài WordPress về tour đó tự chuyển về nháp sau 7 ngày (comment ngày 06/11).
> - **Từ nay:** đại lý nhận chuông và email liệt kê các bài WordPress liên quan. Trong Content studio có danh sách các bài này; đại lý bấm "Move to draft" một lần cho từng bài nếu muốn ẩn. Khi đại lý chưa bấm, bài vẫn ở trên website.
> - **Đại lý muốn tự động** thì bật "Automatically move posts about a discontinued tour to draft" trong Account settings và chọn số ngày. Mặc định tắt. Bài trên Facebook không bao giờ bị sửa.
> - **Khi Adventure Asia bán lại tour:** đại lý bấm "Put back online" để đăng lại từng bài, như comment trước.
> - **Đã kiểm trên Dev:** thẻ cài đặt và danh sách bài hiện đúng. Đã chạy trọn vòng trên site WordPress thử: Adventure Asia ngừng bán tour → bài vẫn ở trên website, đại lý nhận chuông và danh sách bài → đại lý bấm "Move to draft" → bài thành nháp → Adventure Asia bán lại tour → đại lý bấm "Put back online" → bài lên lại. Mọi bước đạt.
>
> Ảnh: thẻ "Discontinued tours" trong Account settings của đại lý thử Atlas & Hearth.

Ảnh đề xuất (1 ảnh): `ui-verify/03b-studio-studio-account-settings-1440-light.png` → `studio-tour-ngung-ban.png`.
Ảnh có ô email đăng nhập đã được che xám sẵn. Không dùng các ảnh `03a/03b-owner-*` (tài khoản chủ CRM không có Content
studio, trang "No Content studio access").

| Câu | Bằng chứng |
|---|---|
| Trước đây tự chuyển sau 7 ngày | comment 10616 (06/11) |
| Không tự sửa; chuông + email; danh sách; "Move to draft"; mặc định tắt; Facebook không đổi | AA-Partner #262 (`91256719`); chữ trên trang `03b`: "Off by default … your WordPress pages stay online until you act … Facebook posts are never changed." |
| "Put back online" | comment 10633; AA-Partner #256 |
| Thẻ cài đặt và danh sách hiện đúng | ảnh `03b-studio-studio-account-settings`, `03a-studio-studio-publish` (1440 + 390 tối) |
| Vòng đầy đủ trên WordPress thử chưa xong | phiên điều phối: vòng đầy đủ đang chạy / chưa xong lúc soạn. Nếu xong trước khi đăng: sửa dòng cuối thành kết quả thật + thêm ảnh |

---

## Nháp 3 — PR-24 "TripPlanner"

Vì sao: comment 10627 (08/11) báo lead của đại lý vào đúng CRM; hôm nay phần lịch trình của từng đại lý được tách ở tầng
cơ sở dữ liệu và đã thử trên trang của 2 đại lý thử.

Đăng ở: comment mới trên PR-24.

> @thule Cập nhật TripPlanner ngày 10/11 (Dev):
>
> - **Dữ liệu lịch trình của mỗi đại lý được tách hẳn ở tầng cơ sở dữ liệu:** trang TripPlanner của đại lý này không đọc được lịch trình của đại lý khác. Việc tách do cơ sở dữ liệu tự áp, không phụ thuộc từng màn hình. Một bài kiểm tự động chạy mỗi đêm; lần chạy 10/11 đạt 99/99 mục.
> - **Đã thử trên trang TripPlanner của 2 đại lý thử:** lập lịch trình rồi tải lại trang: lịch trình còn nguyên, và không lẫn sang trang của đại lý kia.
> >
> Ảnh: trang TripPlanner của đại lý thử Terra Family Expeditions sau khi tải lại, lịch trình vẫn còn.

Ảnh đề xuất (1 ảnh): `aa1038-force-smoke/terra-4-after-reload.png` → `tripplanner-dai-ly-sau-tai-lai.png`.

| Câu | Bằng chứng |
|---|---|
| Tách ở tầng cơ sở dữ liệu, 99/99 mỗi đêm | phiên điều phối S276 (bài kiểm cách ly chạy hằng đêm, lần 10/11: 99/99) |
| 2 đại lý thử, tải lại, không lẫn | `aa1038-force-smoke/` (`aa-1…4b`, `terra-1…4b`, `cross-aa-context-after-terra-trip.png`) |
| 12–14 USD/tháng | phiên điều phối S276. **Tech lead kiểm trước khi đăng:** riêng phần gắn nhãn TripPlanner trong `aa1038-cost/ce-app-daily.json` (01–09/11) là 0,80 USD, khoảng 2,7 USD/tháng; con số 12–14 USD hẳn đã gồm phần chia của hạ tầng dùng chung. Nếu không chắc, bỏ dòng chi phí |

---

## Nháp 4 — PR-22 "CIS — Nội dung & pipeline"

Vì sao: tiếp comment 10631 (chất lượng viết) và 10622 (bài blog dưới ngưỡng). Hôm nay đổi cách dựng phần cố định của tour
AA và có kết quả rà soát mới cho bài blog của đại lý.

Đăng ở: comment mới trên PR-22.

> @thule Cập nhật nội dung tour và bài viết ngày 10/11 (Dev):
>
> - **Viết lại tour của Adventure Asia:** các phần cố định (số ngày, tiêu đề từng ngày, dòng bữa ăn và nơi ngủ) nay do hệ thống dựng thẳng từ file nguồn; AI chỉ viết phần văn mô tả. Nhờ vậy các phần này luôn khớp nguồn.
> - **Thử thật trên 3 tour:** cả 3 đạt, 0 lỗi so với nguồn, khoảng 0,05 USD mỗi tour.
> - **Kiểm miễn phí trên 817 tour đang có:** không có thay đổi ngoài dự kiến, và tìm ra 280 tour có phần cố định cần sửa. Các tour này sẽ được sửa theo từng đợt.
> - **Bài blog cho đại lý:** trên lô thử mới nhất (28 bài blog của 4 đại lý thử), lý do hàng đầu khiến bài dưới ngưỡng là bài ngắn hơn độ dài yêu cầu (13 trong 20 bài dưới ngưỡng). Cách sửa hiện nay là viết lại cả bài, ít hiệu quả. Đã lên kế hoạch thay bằng một bước viết bổ sung phần còn thiếu từ dữ kiện có sẵn. Đại lý vẫn nhận bài như thường; mức "dưới ngưỡng" chỉ hiện trong Writing Lab.

| Câu | Bằng chứng |
|---|---|
| Phần cố định dựng từ nguồn, AI chỉ viết phần văn | phiên điều phối S276 (bước viết lại tour AA đã ship + deploy) |
| 3 tour, cả 3 đạt, 0 lỗi, ~0,05 USD/tour | phiên điều phối S276 (thử thật 3 tour) |
| 817 tour, không thay đổi ngoài dự kiến, 280 tour cần sửa | phiên điều phối S276 (chạy lại miễn phí); cách sửa: `master-propagation/README.md` (nghiên cứu, chưa chọn đường sửa) |
| 28 bài blog, 4 đại lý thử, 13/20 vì quá ngắn | `docs/audits/2026-11-10-S276-aa741-phase3/README.md` §1 mục 1 (`o1 PIECES`, `o1 SUM_F4`) |
| Viết lại cả bài ít hiệu quả; thay bằng bước viết bổ sung | cùng file §1 mục 2 (18 bài viết lại, chỉ 2 đạt; đề xuất "extend repair") |
| Đại lý vẫn nhận bài | luật "tenant sees content only" (bài dưới ngưỡng chỉ là tín hiệu Writing Lab) |

Không đưa vào comment (theo dặn: chỉ số mỗi tour): chi phí mỗi bài blog đạt, chi phí lượt viết lại, các phát hiện vận
hành khác của rà soát T-series (lượt sửa thương hiệu bị cắt, thị trường bị bỏ, bước Debate) — để tech lead quyết khi
lên kế hoạch sửa. Nếu muốn nói rõ hơn với chị: câu "lô 09/11 nêu lý do hàng đầu là câu kêu gọi hành động" (comment 10622)
đo trên lô khác (151 bài, 9 đại lý), hai số không mâu thuẫn.

---

## Không soạn nháp riêng (lý do)

| Việc | Lý do |
|---|---|
| Báo cáo tuần PR-20 kỳ 4 (03–09/11) | ĐÃ ĐĂNG 09/11 06:35 (comment 10625 trên PR-20) |
| Báo cáo tuần PR-20 kỳ 5 (10–16/11) | Chưa hết kỳ; soạn cuối tuần từ S274 → các phiên tới |
| PR-25 Booking | Phiên này không có thay đổi Booking riêng; trang "Bookings with AA" là phần CRM (Nháp 1) |
| Trang so sánh Odoo / CRM / Booking (73 dòng) | Không đưa vào PR-26: trang có cột mã issue nội bộ, tên bảng / file code, và các dòng làm hôm nay (thanh toán, huỷ, lãi lỗ) vẫn ghi "đang làm"; con số 73 dòng cũng khác 53 tính năng đã báo trong 10635 (73 gồm thêm các dòng "mình hơn Odoo"). Nếu tech lead muốn gửi, nên làm bản cho chị (bỏ mã issue và tên kỹ thuật, cập nhật trạng thái) rồi mới mở quyền xem |
| PR-27 / hạ tầng | Không soạn comment hạ tầng (luật: không đưa quyết định kỹ thuật lên Jira) |

## Ghi chú cho tech lead trước khi duyệt

1. **Bảng phí huỷ gợi ý khác câu 3A một chút:** câu 3A (đã đăng 10636) không có mức nào cho huỷ từ 31 ngày trở lên (tức
   0%), bản code thêm 10%. Nháp 1 nói rõ điều này. Nếu muốn khớp đúng 3A, đổi mức 31 ngày về 0% trong code trước khi
   đăng, rồi sửa câu trong nháp.
2. **Chi phí TripPlanner** (Nháp 3): kiểm lại con số 12–14 USD/tháng như ghi ở bảng bằng chứng.
3. **PR-23** (Nháp 2): nếu vòng đầy đủ trên site WordPress thử xong trước lúc đăng, thay dòng cuối bằng kết quả thật.

## Thứ tự đăng đề xuất (khi tech lead duyệt)

1. PR-26: Nháp 1 (4 ảnh).
2. PR-23: Nháp 2 (1 ảnh).
3. PR-24: Nháp 3 (1 ảnh).
4. PR-22: Nháp 4.

Trạng thái đăng: chưa đăng (chờ duyệt).
