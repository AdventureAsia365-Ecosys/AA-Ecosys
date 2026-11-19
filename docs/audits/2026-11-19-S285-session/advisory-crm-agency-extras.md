# CRM (AA-Partner): đại lý bán dịch vụ riêng (vé máy bay, visa)

## 1) Trả lời ngắn

- **Hiện tại CRM không chỉ cho ghi văn bản.** Đại lý đã có dòng dịch vụ có cấu trúc: nhà cung cấp riêng, danh mục dịch vụ có giá, phương án "agency" trong proposal builder, booking line `supplier_kind='agency'` có trạng thái, số xác nhận, tiền (cost/sell/commission), voucher có PNR, e-mail gửi nhà cung cấp và tracker visa.
- **Không có tích hợp ngoài nào** (GDS, hãng bay, API visa). Thứ duy nhất chạm ra ngoài là một link FlightAware công khai (`apps/AA-Partner/api/app/workflows/tasks.py:40`). Như vậy luật (c) đang được giữ.
- **Dòng của đại lý không bao giờ sang AA Booking.** Đồng bộ với Booking và bước release cho ops chỉ lấy dòng `aa`.
- **Còn 7 lỗ hổng:**
  - Proposal được chấp nhận không tự tạo dòng agency, đại lý phải gõ lại.
  - Không có loại block/nhóm "dịch vụ thêm".
  - Vẫn gõ được khách sạn/hoạt động riêng, trái luật (a).
  - File đính kèm và hạn xử lý chưa gắn được vào từng dòng.
  - Hóa đơn chỉ hiện dòng agency dưới dạng tiêu đề, không có giá.
  - Mỗi booking line bắt buộc phải có nhà cung cấp.
  - `transfer` đang xung đột với luật (a).
- **Khuyến nghị:** giữ cách làm thủ công có cấu trúc, khóa danh sách đóng (flight, visa, insurance, fee; transfer chờ chốt) và lấp 7 lỗ hổng trên trong 4 phiên. Không phát sinh chi phí AWS mới.

## 2) Hiện trạng

| Thành phần | Trạng thái | Bằng chứng |
|---|---|---|
| Nhà cung cấp riêng (kind `own`) | Có, nhưng danh mục còn mở (accommodation, activity, guide, restaurant, transport, dmc) | `docs/architecture/db-schema-reference.md:5407`, `apps/AA-Partner/api/app/ledger/suppliers.py:29-40`, form mặc định `accommodation` `web/components/ledger/SuppliersView.tsx:139` |
| Danh mục dịch vụ riêng có giá | Có: flight/insurance/visa/transfer/fee, net/sell, bậc giá theo số khách | `db-schema-reference.md:5348`, `api/app/catalogue/service.py:35` |
| Phương án agency trong builder | Một phần: có tiêu đề, giá bán, giá net; không kiểm loại block hay danh mục | `api/app/proposals/builder.py:1338-1370` |
| Loại block cho flight/visa | Thiếu | `api/app/proposals/rules.py:27` |
| Accept → booking line agency | Thiếu: chỉ ghi dòng AA | `api/app/booking/proposal_lines.py:1-22, 146-212` |
| Booking line agency | Có: planning→requested→confirmed→cancelled, số xác nhận, ngày dịch vụ | `db-schema-reference.md:5797-5870` |
| Booking line phải có nhà cung cấp | Có, là vấn đề: `agency_supplier_id` NOT NULL, đại lý tự làm visa vẫn phải tạo "supplier" | `db-schema-reference.md:5803` |
| Tiền, FX, hoa hồng | Có: bảng tiền chỉ ghi thêm, tỷ giá chốt lúc confirm, `crm.commission` theo dòng | `db-schema-reference.md:5872-5905, 6290-6296` |
| Voucher, PNR | Có: `pnr_enc` | `db-schema-reference.md:5907-5925` |
| E-mail yêu cầu đặt dịch vụ | Có: gửi từ hộp thư đại lý, không phải tích hợp | `apps/AA-Partner/CONTEXT.md:1167-1187` |
| Tracker visa | Có, nhưng không nối với dòng bán hay tiền | `db-schema-reference.md:10456-10490` |
| Chuyến bay của khách | Một phần: chỉ chuyến đến/đi, không vé, không giá | `db-schema-reference.md:9895-9925` |
| File đính kèm (kind `ticket`) | Một phần: chỉ gắn với trip hoặc traveller | `db-schema-reference.md:6592-6621` |
| Hạn xử lý (task) | Một phần: chỉ gắn với trip hoặc client | `db-schema-reference.md:9426, 9460` |
| Hóa đơn cho khách | Một phần: dòng agency là "included", không có giá | `api/app/invoices/service.py:624-631`, `CONTEXT.md:2350-2356` |
| Không sang AA Booking | Có | `api/app/booking/sync.py:126,190,207`, `api/app/ops_release/service.py:65,105,448` |

## 3) Chuẩn thị trường

- **Phần mềm DMC/tour operator (Tourplan, Lemax):** mỗi dịch vụ là một "service line" có loại (vé máy bay, visa, phí), có nhà cung cấp, cost/sell, trạng thái, voucher. Báo giá tách theo nhóm dịch vụ.
- **Bókun:** dịch vụ thêm là "extras" gắn vào sản phẩm.
- **CRM cho đại lý (TravelJoy, Tern, Travefy, Umapped):**
  - Vé máy bay được nhập tay: hãng, số hiệu chuyến, giờ, mã đặt chỗ, đính kèm e-ticket.
  - Visa là một checklist kèm tài liệu, phí visa là một dòng giá.
  - Một số tool có tra chuyến bay qua API dữ liệu bay. Ta bỏ phần này theo luật (c).
  - Đặt vé và nộp visa vẫn làm ở công cụ bên ngoài. CRM chỉ ghi lại kết quả.

Kết luận: thiết kế hiện tại của CRM đúng hướng thị trường. Chỉ cần làm chặt và nối các phần đang rời nhau.

## 4) Khuyến nghị và thiết kế

**App sở hữu:** AA-Partner, schema `crm`, migration `crm-NNN` chạy qua DB Migrate. AA-Booking và CIS không đổi gì.

**a. Danh sách đóng, áp một nơi.** Gom chung với đề xuất sáng nay thành một PR CRM + bản sửa ADR 0019 b6, theo `docs/audits/2026-11-19-S285-session/advisory-content-activities-hotels-critic.md:31`.
- Thêm cột `category` vào `crm.option` và `crm.booking_line`.
- Ràng buộc CHECK:
  - Với `source='agency'` / `supplier_kind='agency'`: `category IN ('flight','visa','insurance','fee'[, 'transfer'])`.
  - Với dòng AA: `category` để NULL.
- Thu hẹp `agency_supplier_category_chk` về đúng danh sách trên, cộng thêm `other`.
- Thêm block type `extras` ("Dịch vụ của đại lý"). `add_agency_option` từ chối mọi block khác.
- Các block lodging, activity, transport, meal, guide chỉ nhận phương án AA.

**b. Accept → dòng agency tự sinh.**
- `write_lines` ghi thêm mỗi phương án agency đã chọn thành một booking line `agency`, trạng thái `planning`.
- Chép theo `category`, sell, net, nhà cung cấp, kèm `option_id` để truy ngược.
- Hết phải nhập hai lần. Giá trong sổ khớp với giá khách đã đồng ý.

**c. Đại lý tự làm.**
- Cho `agency_supplier_id` được NULL khi `supplier_kind='agency'`. NULL nghĩa là "đại lý tự làm".
- Nhà cung cấp có thể chọn từ danh bạ của đại lý hoặc để trống. Không bao giờ được chọn dòng AA.

**d. File đính kèm, hạn xử lý, visa.**
- Thêm cột nullable `booking_line_id` vào `crm.document`, `crm.task`, `crm.visa_application`. Dòng phải cùng trip.
- Thêm document kind `visa_letter`.
- Booking line có thêm `due_at` (hạn xuất vé hoặc hạn nộp hồ sơ). Job hiện có mở task `agency_line_due` khi gần hạn, theo cách của `visa_deadline_overdue`.

**e. Báo giá, hóa đơn cho khách.**
- PDF proposal và hóa đơn tách hai nhóm: "Tour (Adventure Asia)" và "Dịch vụ do [tên đại lý] cung cấp", kèm một câu miễn trừ (đại lý chịu trách nhiệm, theo b5).
- Dịch vụ bán thêm sau khi đã accept: tạo hóa đơn "add-on" từ các dòng agency đã chọn. Dòng có giá, `source='agency_line'` (đã có trong CHECK `db-schema-reference.md:7166`).

**f. Quyền.**
- Giữ nguyên RLS tiền (chỉ owner/agent) và cơ chế reveal tài liệu có lý do.
- Visa: AI không tư vấn (`CONTEXT.md:3026-3040`).
- Thêm test: dòng có `category` không bao giờ lọt vào sync Booking hay ops release.

**g. Vé máy bay (bước sau).** Thêm vài trường chặng bay có cấu trúc (hãng, số hiệu, sân bay, giờ) vào dòng `flight`. Có nút "dùng làm chuyến đến/đi" để chép sang `crm.traveler_flight`, cho AA ops lấy giờ đón. Hoàn toàn nhập tay, không gọi API.

## 5) Lộ trình

| Phiên | Bước giao được | Ngày công |
|---|---|---|
| 1 | Mục a: migration, guard builder, form supplier, sửa ADR 0019 b6. Đếm dữ liệu Dev trước khi thu hẹp CHECK. | 1,5 |
| 2 | Mục b + c: accept sinh dòng agency, supplier được NULL, chip danh mục trên LinesPanel | 1,5 |
| 3 | Mục d: liên kết tài liệu/task/visa với dòng, `due_at`, task tự mở | 1,5 |
| 4 | Mục e: PDF tách nhóm, hóa đơn add-on có giá | 1 |
| 5 (tùy chọn) | Mục g: chặng bay có cấu trúc, chép sang `traveler_flight` | 1 |

- **Chi phí:** 0 USD AWS mới (dùng RDS/ECS sẵn có), không gọi LLM.
- **Rủi ro:** các phiên 1–3 có migration và schema, nên cần một agent review trước khi merge.

## 6) Câu cần chốt

1. **Transfer có còn là dịch vụ của đại lý không?** (business owner)
   Đề xuất: chỉ cho đưa đón sân bay ngoài ngày tour (trước/sau tour). Mọi xe trong tour phải do AA. Nếu khó giải thích với đại lý thì bỏ hẳn.
2. **Giữ insurance và fee như b6 không?** (business owner)
   Đề xuất: giữ.
3. **Đại lý muốn thêm đêm khách sạn trước/sau tour thì làm sao?** (business owner)
   Đề xuất: không cho đại lý tự thêm. Gửi yêu cầu cho AA, theo luật (a) và `advisory-hotels.md`.
4. **Dịch vụ của đại lý hiện giá riêng hay gộp vào giá tour trên báo giá?** (tech lead)
   Đề xuất: mặc định hiện giá riêng, có tùy chọn "gộp giá" theo từng proposal.
5. **Thể hiện "đại lý tự làm" bằng NULL hay một dòng supplier mặc định?** (tech lead)
   Đề xuất: dùng NULL, giao diện hiện nhãn "Đại lý tự làm".
6. **Nhà cung cấp riêng thuộc các danh mục sắp bị cấm xử lý thế nào?** (tech lead)
   Đề xuất: trên Dev chưa có tenant thật, nên chuyển hết sang `other` và đánh dấu inactive trong cùng migration.
7. **Làm chặng bay có cấu trúc (phiên 5) ngay hay chờ?** (tech lead)
   Đề xuất: chờ phản hồi của đại lý pilot. PNR và e-ticket đính kèm tạm thời là đủ.
