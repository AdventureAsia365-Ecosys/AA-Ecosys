# Vòng 2: lên lại kế hoạch theo phiên (T14)

_S285, 19/11/2026. Tư vấn cho tech lead, chỉ đọc code, không sửa repo. Dựa trên các bản `advisory-*.md` cùng thư mục và
quyết định trên trang chốt S285 (B1, B3–B13 và T1–T19 đã "yes"; **B2 bị "no"**, đang chờ đề xuất mới)._

---

## T14. Thứ tự làm, tính theo phiên thay cho ngày công

**Câu hỏi của tech lead:** plan cũ ghi 16–23 ngày công mỗi khối, nghe rất nặng. Thực tế chỉ có một kỹ sư (tech lead)
duyệt, còn Claude Code chạy nhiều lane song song dưới Ultracode. Cần một kế hoạch thực tế hơn.

### 1) Trả lời ngắn

- Toàn bộ việc đã duyệt gom lại thành **10 lát việc**, mỗi lát là **1 issue Linear** và 1 PR hoặc một nhóm PR nhỏ.
- Làm xong trong khoảng **4 phiên**, cộng **1 phiên dự phòng** (tổng 4–5 phiên). Nếu mỗi ngày làm việc một phiên thì
  mất khoảng 1–1,5 tuần, khi không có việc khác chen vào.
- Tech lead chỉ cần làm 3 việc: (1) duyệt danh sách đầu mỗi phiên, (2) duyệt **tiền**, (3) chốt **quyết định** còn treo.
  Ở giai đoạn dev, review code và review migration do agent làm.
- Thứ tự: **migration nền của mỗi app làm trước** (CRM, Booking, CIS chạy song song ngay phiên 1), rồi tới các lát dùng
  migration đó.

### 2) Vì sao con số "ngày công" làm plan nghe ghê

- "Ngày công" (man-day) là thời gian **một người** gõ code. Ví dụ hợp đồng khách sạn 20–23 ngày công nghĩa là một lập
  trình viên mất khoảng 1 tháng.
- Với lane thì khác. **Lane** là một luồng việc riêng: một agent viết code trong một **worktree** (bản sao riêng của
  repo, không đụng bản chính), sau đó hai agent khác review theo hai góc (đúng spec, và bảo mật/dữ liệu), rồi agent đầu
  sửa theo review. Điều phối (orchestrator, phiên Claude Code chính) mở PR, merge và deploy.
- Lane không bị chậm vì gõ code. Thứ làm chậm là ba chỗ:
  1. **Chuỗi migration:** viết migration → chép sang repo Infra → chạy **DB Migrate** (workflow áp migration lên DB Dev,
     phải đợi các bảng job rảnh) → mới merge được code dùng cột mới. Mỗi chuỗi mất khoảng 20–40 phút và phải chạy lần lượt.
  2. **RAM của máy:** tối đa **3 lane nặng** chạy cùng lúc (theo `skill/aa-session/references/parallel-lanes.md`).
  3. **Quyết định của người:** tiền, luật kinh doanh, và câu B2 còn treo.
- Vì vậy nên đếm bằng **phiên** và **lát**, không đếm bằng ngày công. Một phiên (khoảng một ngày làm việc) chạy được
  khoảng 2 đợt, mỗi đợt 3 lane. Mỗi lane mất khoảng 2–4 giờ (ước lượng, phụ thuộc số lần sửa sau review).

### 3) Luật cắt lát (để không vỡ)

- **Một lát = một issue Linear**, thường là 1 PR. Nếu có migration thì là nhóm nhỏ "migration → code".
  Lát nào có migration, quyền hoặc nhiều repo thì mang theo một **spec** (bản mô tả yêu cầu, theo AA-1137).
- **Mỗi app chỉ migrate schema của mình:** CRM viết `crm-NNN`, Booking viết `bk-NNN`, CIS viết số `NNN`. Hiện tại DB đang
  ở CIS 454, bk-059, crm-077 (`docs/architecture/db-schema-reference.md:5`). Điều phối **giữ số trước** cho từng lane
  (dùng tham số `migStart`) để hai lane không cùng lấy một số, ví dụ bk-060 và bk-061.
- **Kiểu "expand trước, contract sau":** chỉ thêm bảng hoặc cột mới, không xoá cột cũ trong cùng đợt. Nếu có sai thì
  quay lại cũng dễ.
- **Không quá 8 issue In Progress cho cả team** (trần WIP tech lead đã đặt). Vì vậy chỉ mở issue của phiên đang chạy,
  không mở cả 10 issue cùng lúc.
- Ảnh chụp giao diện và kiểm live do agent tự làm, không nhờ tech lead.

### 4) Mười lát việc

Cột "Mig" là migration mới (số chính xác do điều phối giữ lúc mở lane).

| # | Tiêu đề Linear (EN) | Gồm các mục | Repo | Mig | Cần làm xong trước |
|---|---|---|---|---|---|
| L1 | CRM: agency lines limited to flight, visa, insurance and fee | B5, B6, B9, B10, B11, T19 + sửa ADR 0019 b6 | Partner (+ root) | crm-078 | không |
| L2 | CRM: agency extras follow the trip from proposal to invoice | T18 (tự tạo dòng, file, hạn, hoá đơn) | Partner | crm-079 | L1 |
| L3 | CIS: tour edits are versioned, locked and published through one review gate | T1, T2, T3 + vá nhanh "phương án A" của `advisory-content-editing.md` (promote phải qua cổng kiểm lại, ô sửa trong drawer hiện theo quyền, ghi audit khi sửa tour gốc, Review Queue sửa được lịch trình) | CIS | CIS 455 | không |
| L4 | CIS: content staff create a tour by hand, tied to an AA supplier | T4, T5 (form có hướng dẫn, view nhà cung cấp) | CIS + Booking | bk view + CIS | L3 |
| L5 | Booking: one supply model for pax types, contract terms, restrictions and allotment | T12, B4, B7 (cột), B8 (bảng), T13 (quyền stop-sale) | Booking | bk-060 | không |
| L6 | Booking: a sold tour becomes one supplier booking per component | T15, T16, B12, B13 | Booking | bk | L5 |
| L7 | Booking: complete supplier profile and a four-role staff matrix | T17, T13 (4 vai trò, **không** thêm `ops`: đổi tên hiển thị `contracting`, ẩn `content_creator`, Kế toán thêm `bill.read` + `payout.write`; chỉ sửa `staff.py`, không migration) | Booking (+ Infra nếu duyệt khoá KMS) | bk | L5 |
| L8 | Booking + CIS: optional activities as AA offers with places and sale rules | PR-29: B1, B3, B4, T7 | Booking + CIS | bk + CIS | L5 |
| L9 | TripPlanner + CRM: optional activities per day for customers and agencies | PR-29: T6 (+ B2 khi chốt lại) | TripPlanner + Partner + Booking | không (hoặc nhỏ) | L8 |
| L10 | Booking: hotel contracts with property master, meal plans, supplements and allotment | PR-30: T8–T11, B7, B8 | Booking | bk | L5 |

**Done-when** (điều kiện để coi là xong; mọi lát đều kiểm trên Dev, sau khi merge, CI xanh, deploy xong và gọi được
endpoint live):

- **L1:** API CRM từ chối (4xx) khi thêm phương án đại lý vào block khách sạn, xe, hoạt động, hoặc khi gắn nhãn
  `transfer`/`other` cho một dòng dịch vụ của đại lý (`other` chỉ còn trong danh bạ nhà cung cấp). Các nhà cung cấp
  riêng (`kind='own'`) thuộc loại bị chặn được đếm trước (số ghi trong PR; khoảng 63 là cả bảng, gồm cả dòng
  "Adventure Asia" của mỗi đại lý), đổi sang `other`; dòng không còn dùng vào thùng rác, dòng còn được tham chiếu giữ
  để đọc lịch sử (T19). Nút
  "Nhờ AA báo giá đêm thêm" (B11) tạo được một yêu cầu gửi AA. Facts Entries chỉ còn markup và điều khoản bán (B6).
  ADR 0019 b6 đã sửa.
- **L2:** Chấp nhận một proposal có 1 vé máy bay và 1 visa của đại lý thì tự sinh 2 dòng của đại lý. Hoá đơn PDF có
  nhóm riêng "Dịch vụ do <đại lý> cung cấp". Dòng sắp tới hạn tự mở task. Có test chứng minh không dòng nào của đại lý
  đi sang Booking.
- **L3:** Sửa câu chữ một tour tạo ra phiên bản mới, có diff (so sánh khác biệt) với bản đang chạy, bấm xuất bản thì
  TripPlanner thấy ngay. Chạy lại một wave thì bỏ qua tour đã khoá. Import lại Excel thì hiện khác biệt từng trường và
  bản sửa tay thắng (T1). Đổi sự thật tour thì T2 của đại lý đang dùng tour chạy lại (bản đại lý chưa tự sửa thì tự
  thay, bản đại lý đã tự sửa thành bản chờ), có ghi vào `shared.llm_call_log`, và dừng khi chạm trần tháng (T3).
- **L4:** Một nhân viên content tạo được một tour 3 ngày từ trang trống, chọn nhà cung cấp AA từ danh sách của Booking.
  Tour qua cổng duyệt (trên Dev người tạo tự xuất bản theo T2; bật công tắc "cần người thứ hai" thì content_lead
  duyệt) rồi vào luồng Review như tour đến từ Excel. Có báo cáo các tour cũ có `provider` dạng
  chữ chưa nối được với ID.
- **L5:** Một hợp đồng thử có giá trẻ em 50 %, điều khoản huỷ theo bậc và stop-sale (ngừng bán) ngày 24/12. Giá tính
  đúng: dòng trẻ em bằng 50 %, ngày 24/12 ra "on request" (hỏi lại nhà cung cấp). contracting đặt được stop-sale; sales
  bị 403.
- **L6:** Đại lý xác nhận đặt một tour 5 ngày (4 đêm khách sạn, 5 chặng xe, 1 hướng dẫn viên); điều hành bấm Generate
  thì sinh ra 10 đặt dịch vụ với nhà cung cấp, lấy từ snapshot (bản chụp) lúc xác nhận. Sửa tour sau đó không làm đổi
  đơn đã bán. Tour thiếu khách sạn đêm 2 bị chặn bán B2B (luật N1), admin mở ngoại lệ được nhưng phải ghi lý do (B13).
  Thiếu xe ngày đổi điểm chỉ ra cảnh báo (N4), không chặn.
- **L7:** Một nhà cung cấp có 3 người liên hệ theo vai trò; đơn đặt hàng gửi tới người phụ trách đặt chỗ. Sales chỉ thấy
  số tài khoản đã che; Kế toán (`finance`) và Quản trị thấy đủ. Đổi số tài khoản phải chờ người thứ hai duyệt. Hạn thanh
  toán hoá đơn tự tính theo hợp đồng. Kế toán ghi được khoản trả tiền nhà cung cấp; không có vai trò `ops`.
- **L8:** Import một file 5 hoạt động thì tạo ra 5 bản nháp; người thứ hai publish. View `v_place_addons` chỉ trả về
  những ngày có giá còn hạn (B3). Giá trẻ em tính theo B4. Admin thấy cảnh báo hợp đồng sắp hết hạn trước 60 ngày (job nhắc hết hạn
  làm một lần cho mọi hợp đồng nhà cung cấp; L10 chỉ thêm phần nhắc xác nhận lại khách sạn).
- **L9:** Thẻ ngày "HCMC" trên TripPlanner hiện ít nhất 1 hoạt động thêm. Khách tick chọn thì lead (yêu cầu khách gửi)
  mang theo mã `sv:`. Đại lý báo giá hoạt động đó trong CRM bằng drawer "AA add-on". Phần hiện giá trên trang của đại lý
  để tắt cho tới khi B2 chốt lại.
- **L10:** Một khách sạn có 2 hợp đồng của 2 DMC (nhà cung cấp). DMC thứ hai gửi bảng "giá công bố 70 USD, hoa hồng
  20 %": importer tự quy ra net 56 USD và giữ hai số gốc (B7: mọi giá lưu theo net, không có luồng hoa hồng riêng).
  Đặt phòng gửi tới DMC của hợp đồng chứa dòng giá đã dùng (T8). Báo giá 3 đêm HB
  (half board: phòng kèm bữa sáng và bữa tối) cho 2 người lớn và 1 trẻ 7 tuổi ra đúng giá vốn. Allotment (số phòng nhà
  cung cấp giữ sẵn) 2 phòng, release 7 ngày (quá hạn này thì phòng giữ sẵn trả lại): phòng thứ 3 ra "on request".

Vài điểm nhỏ cần nói rõ:

- **L5 là móng chung.** Bảng restriction/allotment chung, điều khoản huỷ và điều khoản thanh toán có cấu trúc trên hợp
  đồng, `pax_type` trên giá: đều làm một lần ở L5, rồi hoạt động (L8), khách sạn (L10) và tour (L6) dùng chung. Đây là
  cách thu gọn mạnh nhất so với plan cũ. Plan cũ có 3 bản tư vấn, mỗi bản tự làm phần giá trẻ em, huỷ và stop-sale riêng.
- **Ghi chú của tech lead ở T16 (làm tròn số xe rủi ro):** L6 chỉ dùng công thức `số xe = làm tròn lên(số khách / số
  chỗ)` làm **giá trị gợi ý**. Nhân viên hoặc khách vẫn sửa được số lượng (ví dụ khách muốn 2 xe cho 4 người). Số lượng
  lưu là số người chốt, không phải số máy tự tính.
- **L7 có tiền:** số tài khoản ngân hàng cần mã hoá. Booking chưa có khoá KMS riêng: code ghi "a new paid key waits for
  its own approval" (`apps/AA-Booking/backend/app/ops/files.py:10`). Một khoá KMS mới tốn khoảng 1 USD/tháng cộng phí
  gọi rất nhỏ. Nếu chưa duyệt thì L7 làm hết phần khác và để phần ngân hàng sau.
- **L9 có quyết định treo:** B2 (giá hoạt động trên trang của đại lý, có làm tròn không) bị "no". L9 vẫn làm được phần
  hiển thị và báo giá trong CRM. Phần hiện giá để sau một cờ (feature flag) tắt cho tới khi chốt.

### 5) Lịch theo phiên

Tối đa 3 lane nặng chạy cùng lúc. Lane nhỏ vào ngay khi một lane xong.

| Phiên | Lane chạy song song | Migration áp trong phiên | Ghi chú |
|---|---|---|---|
| **1. Móng** | L1 (CRM), L5 (Booking), L3 phần 1 (CIS: vá nhanh + bảng phiên bản + khoá) | crm-078, bk-060, CIS 455 | 3 app khác nhau nên không đụng nhau. Còn thời gian thì mở L2. |
| **2. Dùng móng** | L2 (CRM), L6 (Booking), L3 phần 2 (trang Tour editor) | crm-079, bk-061 | L4 vào khi một lane xong. |
| **3. Nguồn cung** | L4 (nếu chưa xong), L8 (hoạt động), L10 phần 1 (khách sạn), L7 | bk-062..064, CIS 456–457 | Nhiều migration Booking: điều phối xếp chuỗi lần lượt. |
| **4. Tới khách** | L9 (TripPlanner + CRM), L10 phần 2 (allotment, Excel 2 chiều), một lượt UI smoke (kiểm nhanh mọi trang mở được, không lỗi) + ảnh chụp toàn bộ | ít | Đóng issue theo `aa-ship`. |
| **5. Dự phòng** | Sửa sau review, phần giá B2 nếu đã chốt, phần ngân hàng L7 nếu đã duyệt tiền | tuỳ | Không cần thì bỏ. |

Ví dụ một phiên 1 (ước lượng):

- 09:00 mở 3 lane.
- Khoảng 11:30 ba migration đã qua review; điều phối áp lần lượt, mỗi cái khoảng 20–40 phút.
- Khoảng 14:00 merge code dùng migration.
- Chiều: mở L2 và kiểm live.

Tech lead chỉ cần khoảng 15–30 phút đầu phiên để duyệt danh sách và spec, cùng vài phút khi có câu hỏi tiền.

### 6) Phần nào cần tech lead (rút gọn)

| Khi nào | Việc | Ví dụ |
|---|---|---|
| Đầu mỗi phiên | Duyệt danh sách issue + spec của phiên (duyệt một lần, không duyệt từng PR) | "Phiên 1: L1, L5, L3" |
| Phiên 2 (L3) | Đặt **trần tiền tháng** cho việc tự chạy lại T2 (T3) | Đề xuất 10 USD/tháng trên Dev. Mức chính xác lấy từ chi phí thật/tour trong `llm_call_log` trước khi đặt. |
| Phiên 3 (L7) | Duyệt **khoá KMS mới** (KMS = dịch vụ khoá mã hoá của AWS) cho tài khoản ngân hàng (~1 USD/tháng), hoặc lùi phần này | "yes/no" trên trang quyết định |
| Trước phần giá của L9 | Tech lead chốt lại **B2** (đề xuất mới: phương án C trong `advisory-r2-b2b-crm.md`; hỏi business owner nếu thấy cần) | Trang quyết định vòng sau |

**Không** cần tech lead: review code, review migration (agent review độc lập theo luật giai đoạn dev), merge, deploy,
chụp ảnh, kiểm live.

### 7) Thị trường làm thế nào

- Các nhóm nhỏ thường làm theo kiểu **lát dọc**: mỗi lát chạy được từ DB tới giao diện. Họ đổi DB theo kiểu
  **expand/contract** (thêm trước, bỏ sau) và giấu phần chưa xong sau **feature flag** (công tắc bật/tắt tính năng).
  Đây là cách làm phổ biến, không gắn với một hãng cụ thể.
- Với hệ thống ngành du lịch (Tourplan, Lemax...), tôi không có số liệu chắc chắn về cách họ chia đội. Phần này **không
  dùng làm căn cứ**.

### 8) Rủi ro và cách giảm

- **Chồng số migration** giữa các lane: điều phối giữ số trước bằng `migStart`, và chỉ áp tuần tự.
- **L5 quá to:** nếu review thấy nặng thì tách làm 2 PR (bảng + engine). Vẫn là 1 issue.
- **Việc khác chen vào** (AA-1126, AA-1135, AA-1138 đang mở): mỗi phiên dành cho plan này tối đa 1–2 slot cho việc cũ.
  Nếu chen nhiều thì cần thêm 1 phiên.
- **Dữ liệu thật trên Dev chưa đếm hết** (số service `activity`, khách sạn): lane đầu của L8 và L10 đếm trước khi đổi.
  Dữ liệu giả thì xoá theo quy trình DRY RUN (chạy thử trước khi xoá thật).

### Đề xuất cuối

- Chốt **10 issue L1–L10** như bảng trên. Tạo issue Linear theo phiên, không tạo cả 10 issue một lúc.
- Làm trong **4 phiên + 1 dự phòng**. Phiên 1 chạy móng song song: **L1 (CRM), L5 (Booking), L3 phần 1 (CIS)**.
- Tech lead chỉ duyệt danh sách đầu phiên, trần tiền cho T3, khoá KMS của L7, và chốt lại B2 trước phần giá của L9.
- Các bảng "ngày công" trong 4 bản tư vấn vòng 2 khác chỉ để so độ lớn; lịch thật theo phiên là bảng ở mục 5 trên.
