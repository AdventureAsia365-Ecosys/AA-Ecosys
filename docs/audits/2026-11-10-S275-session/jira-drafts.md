# S275 — nháp Jira (tech lead duyệt 10/11, ĐÃ ĐĂNG)

Phiên 10/11/2026 trên Dev. Mỗi nháp: issue đích, vì sao chọn, nội dung đăng nguyên văn (đăng dạng HTML, `@thule` đổi
thành mention node như skill `aa-jira-update`; bảng markdown đổi sang bảng HTML khi đăng), bảng câu → bằng chứng.

## Rà Jira trước khi soạn (đọc 10/11)

- `project in (PR, KAN, CON) AND statusCategory != Done`: hơn 100 issue (phần lớn KAN/CON là việc nội dung và marketing
  của đội AA, không liên quan phiên này). Issue liên quan: epic PR-22…PR-27, PR-13 (Jev), KAN-90 (DataForSEO).
- **Báo cáo tuần PR-20 kỳ 4 (03–09/11) ĐÃ ĐĂNG** ngày 09/11 06:35 (comment 10625 trên PR-20). Không soạn lại. Việc của
  S274 + S275 vào **kỳ 5 (10–16/11)**, soạn khi hết tuần.
- **Không có issue Jira nào nhắc Odoo / plugin** (JQL `text ~ "Odoo" OR text ~ "plugin" OR comment ~ …` trả 0) → nháp
  phân tích Odoo và bảng câu hỏi đặt ở epic CRM **PR-26**.
- **Nháp S274 chưa đăng**: không issue nào trong PR/KAN/CON được cập nhật sau 09/11 07:00. Ba nháp S274
  (`docs/audits/2026-11-09-S274-session/jira-drafts.md`: KAN-90, PR-22, PR-25) vẫn chờ duyệt, gộp đợt đăng với nháp
  dưới đây. Nháp 1 dưới đây là phần sửa cho nháp KAN-90 của S274, không phải comment riêng.
- Không lặp lại: điều khoản AI cho đại lý (đã báo PR-23 ngày 04/11, gồm việc nhờ luật sư); gỡ phần khách lẻ của Booking
  và mốc xoá dữ liệu 28/11 (đã báo PR-25 ngày 09/11, comment 10628) → không soạn nháp riêng, xem mục cuối.

---

## Nháp 1 — KAN-90 "DataforSEO search spent high : critical" (sửa nháp S274, không đăng riêng)

Vì sao: nháp S274 cho KAN-90 đã có dòng Đức/Pháp/Hà Lan; phiên này đo được kết quả làm mới. Thay dòng
"**Đức, Pháp, Hà Lan** cũng đã làm mới (…)" trong nháp S274 bằng dòng sau, rồi đăng cả nháp S274 một lần:

> - **Đức, Pháp, Hà Lan** cũng đã làm mới (0,96 USD mỗi nước, khoảng 6.100 từ khoá mỗi nước, giữ 94,5% sau lọc độ liên quan). Tỉ lệ địa điểm có dữ liệu tìm kiếm cũ ở ba thị trường này giảm từ 99% xuống 8% (đo 10/11).

| Câu | Bằng chứng |
|---|---|
| 0,96 USD, ~6.100, 94,5% | như nháp S274 (aa1055-live/r2-de-fr-nl-quality.out) |
| 99% → 8% | đo live trong phiên điều phối S275 (data coverage `research.stale_share.<DE/FR/NL>`) — ghi giờ đo khi đăng |

---

## Nháp 2 — PR-23 "Portal tenant — Cổng cho đối tác"

Vì sao: tiếp comment 04/11 (phần "khi AA ngừng bán một tour" mới có trong hệ thống) và 06/11 (thử ngừng bán / bán lại,
"phần chuyển bài WordPress về nháp chưa thử thật"). Phiên này có nút đưa bài trở lại và điều khoản bản v0.6.

> @thule Cập nhật app cho đại lý (Content studio) ngày 10/11 (Dev):
>
> - **Đưa bài trở lại khi tour được bán lại ("Put back online"):** khi AA bán lại một tour đã ngừng bán, đại lý thấy từng trang WordPress của mình đã bị chuyển về nháp vì tour đó, và đưa từng trang trở lại bằng một nút bấm. Hệ thống không tự đăng lại bài nào khi đại lý chưa bấm. Đã lên Dev; chưa thử trọn vòng trên site WordPress thử, đây là bước kiểm tiếp theo.
> - **Điều khoản và Quyền riêng tư (bản nháp v0.6, tiếng Anh và tiếng Việt):** ghi rõ nội dung trong app chỉ do các model Claude viết. Đã kiểm trên trang đang chạy ngày 10/11: https://portal.lumiguides.it.com/legal/partner-terms và https://portal.lumiguides.it.com/legal/privacy. Trang vẫn ghi "Draft — pending legal review".

| Câu | Bằng chứng |
|---|---|
| Put back online, không tự đăng lại | CIS #1417 (`746e95a8`) + AA-Partner #256 (`fe57bda4`) merged + deploy Dev; route put-back trả 401 khi không token |
| Chưa thử trên WordPress thử | đúng như phiên điều phối báo: full test để phiên sau |
| v0.6 EN + VI, chỉ Claude | kiểm live trang legal 10/11 (phiên điều phối) |

Ảnh: chưa có trong thư mục phiên. Nếu phiên điều phối có ảnh màn hình nút "Put back online", đính kèm (1 ảnh).

---

## Nháp 3 — PR-22 "CIS — Nội dung & pipeline"

Vì sao: tiếp comment 09/11 (450 nhãn chấm đầu tiên, 84 câu chờ AA xem, giảm bài blog dưới ngưỡng). Nháp PR-22 của
S274 (dữ liệu catalogue) vẫn chưa đăng: đăng nháp S274 trước, nháp này sau (hai comment riêng, cùng đợt).

> @thule Cập nhật chất lượng viết bài và trang quản trị CIS ngày 10/11 (Dev):
>
> - **Bộ đáp án cho bước tự kiểm dữ kiện đã đủ:** 1.018 câu trong bài đã được xem và gán đáp án. Kiểm lại ngẫu nhiên 91 câu, không câu nào phải đổi đáp án. Bộ này dùng để đo độ chính xác của bước kiểm mỗi khi đổi cách viết hay cách kiểm, nên chất lượng viết luôn đo được.
> - **Chi phí AI theo từng tour, từng bài và từng lượt chạy:** hệ thống nay ghi chi phí AI cho từng tour, từng bài viết và từng lượt chạy, để so được chi phí giữa các cách viết.
> - **Hai cải tiến bộ viết đã bật sau khi chạy thử đạt:** viết lại tour cho đại lý theo luồng nhanh hơn; bài blog có bộ tạo tiêu đề và mô tả SEO riêng.
> - **Trang quản trị:** trang hướng dẫn trong admin nay hiện được ảnh chụp màn hình; Writing Lab có trang xem lại nhãn chấm chất lượng ngay trong admin.
> - Bước kiểm sơ bộ tự động (Jev) cho các câu này: xem comment cùng ngày trên PR-13.

| Câu | Bằng chứng |
|---|---|
| 1.018 câu, 0/91 đổi | phiên điều phối S275 (Writing Lab, bộ đáp án fact checker) |
| Chi phí theo tour / bài / lượt chạy | PR CIS đã merge + deploy (phiên điều phối) |
| Hai cải tiến bộ viết | `.tmp-session/S275/aa1049/t2_trial_report.txt` (`T2_ORCHESTRATOR=linear`, succeeded, qa passed), `seo_trial_report.txt` (`T9_SEO_BUILDER=on`, approved) |
| Ảnh trong hướng dẫn, trang xem nhãn | PR CIS đã merge + deploy (phiên điều phối) |

---

## Nháp 4 — PR-13 "Jev (TypeSafe) — decision layer cho content pipeline"

Vì sao: chị Thư theo dõi việc dùng Jev ở story này (comment 22/10, 23/10). Phiên này đo Jev làm bước kiểm sơ bộ cho câu
trong bài.

> @thule Cập nhật về Jev ngày 10/11 (Dev):
>
> - Jev được thử làm **bước kiểm sơ bộ** cho từng câu trong bài viết của đại lý: câu Jev chắc chắn đúng nguồn thì cho qua ngay, câu còn lại vẫn đi qua bước kiểm đầy đủ.
> - Đo trên bộ câu có đáp án (phần câu giữ riêng, không dùng để chỉnh): khi Jev chắc từ 90% trở lên, nó cho qua khoảng hai phần ba số câu đúng; trong 342 câu được cho qua có 2 câu sai, cả hai thuộc loại gắn nhầm dữ kiện. Thêm một luật bổ sung (bộ chấm cũng phải đồng ý, không có dấu hiệu gắn nhầm) thì 341/341 câu được cho qua đều đúng.
> - Đã dùng cách này để lọc trước 372 câu còn lại của bộ đáp án: 182 câu được cho qua, phần còn lại vẫn qua người duyệt. Bước này chưa bật trong luồng viết bài thật; sẽ bật sau khi viết thành code.
> - Chi phí rất thấp: khoảng 0,00015 USD mỗi câu.

| Câu | Bằng chứng |
|---|---|
| ~2/3 câu đúng được cho qua | `docs/audits/2026-11-10-S275-session/aa1063-jev/jev-shadow-calibration.txt`: held_out p≥0,90 coverage 0,660 (t9_blog 0,675) |
| 340/342, 2 sai `fact.misbinding`; luật kết hợp 341/341 | phiên điều phối S275 xác nhận (comment Linear AA-1063 06:36Z): p≥0,90 → 340/342 (Wilson LB 97,9%), luật "p≥0,90 + panel đa số ok + không lens non-ok misbinding" → 341/341 held-out |
| 372 → 182 cho qua | `.tmp-session/S275/jev/pf-run.out` (0,038 USD), labeller `prefilter:jev090+panel` |
| Chưa bật trong luồng thật | đúng: chỉ shadow + lọc tay; "luật thành code" còn mở trong AA-1063 |
| ~0,00015 USD/câu | ledger `adhoc_aa1063`: 576 lượt, 0,084569 USD → 0,000147 USD/lượt |

---

## Nháp 5 — PR-26 "CRM cho đại lý" — phân tích app Odoo tour/travel

Vì sao: không có issue Jira nào về plugin; phần lớn tính năng học được thuộc CRM của đại lý (bán cho khách lẻ), phần còn
lại thuộc Booking. Đăng trước Nháp 6 (bảng câu hỏi trỏ về comment này).

> @thule Phân tích app Odoo tour/travel (ngày 10/11):
>
> - App này là CRM bán tour cho khách lẻ, nên được so với CRM của đại lý (đại lý bán cho khách của mình). Phần AA làm với đại lý (giá net, khởi hành, giữ chỗ) được so với Booking.
> - **53 tính năng được so, 44 tính năng sẽ làm**, chia thành 10 gói việc trong các phiên tới:
>
> | App | Tính năng so | Đã có | Có một phần | Chưa có |
> |---|---|---|---|---|
> | CRM của đại lý | 35 | 9 | 16 | 10 |
> | Booking (AA với đại lý) | 18 | 0 | 12 | 6 |
>
> - **CRM đã tốt hơn app này ở:** nhận yêu cầu của khách, giữ chỗ có hạn, nhiều loại tiền, hồ sơ hộ chiếu được mã hoá, cổng riêng cho khách, ký điều khoản điện tử.
> - **Làm trước trong CRM, để đại lý bán hằng ngày:** giá theo loại khách (người lớn, trẻ em, em bé, phòng đơn); lịch trả tiền nhiều đợt; nhắc khách trả tiền; bảng phí huỷ; giảm giá cần chủ đại lý duyệt; quy tắc giá theo mùa, theo đoàn, đặt sớm; nút "Đặt ngay" trên trang tour của đại lý; thanh toán online qua cổng thanh toán của đại lý.
> - **Gói đầu tiên đã chạy trên Dev (10/11):** giá theo loại khách (người lớn, trẻ em, phòng đơn) hiện trên trang đề xuất gửi khách; đại lý đặt quy tắc giá theo mùa trong Cài đặt > Giá, giá gợi ý tự cộng theo quy tắc; nhân viên giảm giá trên 10% thì không gửi được cho khách cho tới khi chủ đại lý duyệt. Đã thử trọn vòng trên một đại lý thử (ảnh đính kèm).
> - **Tiếp theo trong CRM:** lãi lỗ từng chuyến; trang "Đặt với AA" (hoá đơn và công nợ với AA); hoa hồng cộng tác viên; điều hành chuyến (danh sách đoàn, voucher, hộ chiếu, visa).
> - **Booking, làm sau CRM:** số khách tối thiểu và hạn chốt bán của ngày khởi hành; tạo ngày khởi hành hàng loạt; nhân viên AA nhập booking thay đại lý; so chi phí dự kiến với hoá đơn nhà cung cấp; báo cáo lãi; giữ chỗ riêng cho đại lý.
> - Giấy phép của app không cho chép code, nên app chỉ được đọc để học tính năng; mọi tính năng được viết lại bằng code của hệ thống mình.
> - Một số giá trị mặc định cho các tính năng này cần chủ doanh nghiệp chọn: xem comment tiếp theo.

| Câu | Bằng chứng |
|---|---|
| B2C CRM → so với CRM đại lý; Booking phần B2B | `docs/research/2026-11-10-odoo-tour-travel-plugin-comparison.md` mục "What changed" |
| 53 / 35 (9/16/10) / 18 (12/6) | research note mục Summary; `.tmp-session/S275/aa1065-summary-vi.txt` |
| 44 sẽ làm, 10 gói việc | phiên điều phối S275 (53 − 9 đã có = 44; 10 work packages trong build plan) |
| CRM tốt hơn / làm trước / tiếp theo / Booking | aa1065-summary-vi.txt (hạng 1–8, CRM tiếp theo, hạng 27–44) |
| Giấy phép OPL-1 | research note mục Plugin overview + Licence |
| Gói đầu tiên chạy trên Dev | AA-1066 Done: Partner #258/#259 `451e5011` live, crm-048; Playwright live 8/8 bước (`aa1066-live/results.md`). Ảnh đính kèm: `aa1066-live/06b-client-discount-line.png` (trang khách: dòng loại khách + giảm giá) |

Link: research note nằm ở repo gốc (chưa merge, tiếng Anh, tên kỹ thuật). Không đưa link vào comment trừ khi tech lead
muốn.

---

## Nháp 6 — PR-26 "CRM cho đại lý" — bảng chọn giá trị mặc định (tech lead yêu cầu, được hỏi)

Vì sao: tech lead yêu cầu riêng; 10 câu từ `.tmp-session/S275/thu-odoo-questions.txt`, viết lại theo dạng form khảo sát
trung tính (memory `thu-questionnaire-style`): theo chủ đề, phương án rõ, đánh dấu đề xuất; không "dạ/ạ/nha", không
tên người. Đăng ngay sau Nháp 5.

> @thule Bảng chọn giá trị mặc định cho các tính năng học từ app Odoo tour/travel (xem comment trên). Mỗi câu có một phương án đề xuất. Trả lời theo số câu và chữ cái (ví dụ "3B"), hoặc "theo đề xuất" cho cả bảng. Hệ thống dùng phương án đề xuất cho tới khi có trả lời; mọi giá trị đổi được sau trên trang quản trị.
>
> **A. Thanh toán và bán hàng của đại lý (CRM)**
>
> 1. Cổng thanh toán online làm trước cho đại lý:
>    - A. VNPay trước, MoMo và OnePay sau, Stripe để sau **(đề xuất)**
>    - B. Stripe trước (thẻ quốc tế), các cổng Việt Nam sau
>    - C. Khác: ___
> 2. Nút "Đặt ngay" trên trang tour của đại lý:
>    - A. Mỗi đại lý tự bật hoặc tắt; mặc định tắt, khách đặt qua nhân viên đại lý **(đề xuất)**
>    - B. Mỗi đại lý tự bật hoặc tắt; mặc định bật
>    - C. Không làm, khách luôn đặt qua nhân viên đại lý
>
> **B. Huỷ, giảm giá, hoa hồng (CRM, giá trị mẫu, mỗi đại lý sửa được)**
>
> 3. Bảng phí huỷ mẫu (tính theo số ngày trước khởi hành):
>    - A. Từ 30 ngày trở xuống: 25%; từ 14 ngày trở xuống: 50%; từ 7 ngày trở xuống: 100% **(đề xuất)**
>    - B. Không có bảng mẫu, mỗi đại lý tự nhập
>    - C. Mức khác: ___
> 4. Mức giảm giá nhân viên đại lý được tự áp, không cần chủ đại lý duyệt:
>    - A. Tối đa 10%; cao hơn thì chủ đại lý duyệt **(đề xuất)**
>    - B. Mọi mức giảm đều cần chủ đại lý duyệt
>    - C. Mức khác: ___
> 5. Cách trả hoa hồng cho cộng tác viên của đại lý:
>    - A. Cho chọn một trong ba cách (phần trăm, số tiền cố định mỗi khách, giá net); mặc định phần trăm **(đề xuất)**
>    - B. Chỉ phần trăm
>    - C. Khác: ___
>
> **C. Ngày khởi hành và giữ chỗ (Booking, AA với đại lý)**
>
> 6. Ngày khởi hành cố định của AA:
>    - A. Tối thiểu 2 khách mới chạy; AA quyết chạy hay huỷ trước 21 ngày; chốt bán trước 14 ngày **(đề xuất)**
>    - B. Số khác: tối thiểu ___ khách, quyết trước ___ ngày, chốt bán trước ___ ngày
> 7. Giữ chỗ riêng cho đại lý lớn trên ngày khởi hành:
>    - A. Có; chỗ chưa bán tự trả lại trước 21 ngày **(đề xuất)**
>    - B. Có, số ngày trả lại khác: ___
>    - C. Không làm
> 8. Nhân viên AA nhập booking thay đại lý (khi đại lý gửi qua email hoặc chat):
>    - A. Có **(đề xuất)**
>    - B. Không, đại lý luôn tự nhập
>
> **D. Dữ liệu khách và báo cáo**
>
> 9. Danh sách tên khách và cách xếp phòng đại lý gửi AA để đặt khách sạn:
>    - A. Có gửi; tự xoá sau khi chuyến đi kết thúc **(đề xuất)**
>    - B. Có gửi; giữ thêm một thời gian sau chuyến đi: ___
>    - C. Không gửi; AA chỉ nhận số khách và số phòng
> 10. Người được xem báo cáo lãi theo booking, theo chuyến và theo đại lý:
>    - A. Chỉ chủ doanh nghiệp và kế toán **(đề xuất)**
>    - B. Thêm quản lý vận hành
>    - C. Khác: ___

| Câu | Bằng chứng |
|---|---|
| Phương án A của mỗi câu | đúng nguyên văn đề xuất trong `.tmp-session/S275/thu-odoo-questions.txt` (câu 1–10) |
| Phương án B/C | thêm khi viết lại thành form, là các lựa chọn khác hợp lý, không phải đề xuất. Câu 6: đổi thứ tự "quyết 21 ngày / chốt bán 14 ngày" cho dễ đọc, số giữ nguyên |
| "Hệ thống dùng đề xuất trong lúc chờ" | câu cuối file gốc ("Bên em vẫn làm theo đề xuất trong lúc chờ") viết lại trung tính |

---

## Không soạn nháp riêng (lý do)

| Việc | Lý do |
|---|---|
| Booking: phần khách lẻ đã gỡ ở mọi app, dọn bảng cuối từ 28/11 | Đã báo PR-25 ngày 09/11 (comment 10628: "gỡ toàn bộ … xoá hẳn sớm nhất từ 28/11"). Nếu phiên này gỡ thêm phần còn sót ở app khác, đưa 1 dòng vào báo cáo tuần kỳ 5 |
| Điều khoản AI cho đại lý trước 12/11, luật sư | Đã báo PR-23 ngày 04/11; tech lead dặn không lặp |
| Báo cáo tuần PR-20 kỳ 4 | Đã đăng 09/11 (comment 10625) |
| Báo cáo tuần PR-20 kỳ 5 (10–16/11) | Chưa hết kỳ; soạn cuối tuần từ S274 + S275 + các phiên sau |

## Thứ tự đăng đề xuất (khi tech lead duyệt)

1. KAN-90: nháp S274 số 1 (đã sửa dòng Đức/Pháp/Hà Lan theo Nháp 1).
2. PR-22: nháp S274 số 2 (giữ điều kiện câu "đảo nhỏ"), rồi Nháp 3.
3. PR-25: nháp S274 số 3.
4. PR-23: Nháp 2. 5. PR-13: Nháp 4 (đã xác nhận số liệu, S275).
6. PR-26: Nháp 5, rồi Nháp 6.

Trạng thái đăng (10/11, sau khi tech lead duyệt; tech lead đổi đích nháp DataForSEO từ KAN-90 sang PR-22):

| Nháp | Issue | Comment |
|---|---|---|
| S274 nháp 1 (+ dòng DE/FR/NL của nháp 1 S275) | **PR-22** (không phải KAN-90) | 10629 |
| S274 nháp 2 (catalogue) | PR-22 | 10630 |
| S275 nháp 3 (chất lượng viết) | PR-22 | 10631 |
| S274 nháp 3 (Booking) | PR-25 | 10632 |
| S275 nháp 2 (put back online, pháp lý v0.6) | PR-23 | 10633 |
| S275 nháp 4 (Jev) | PR-13 | 10634 |
| S275 nháp 5 (Odoo + gói đầu tiên, 1 ảnh) | PR-26 | 10635 |
| S275 nháp 6 (bảng chọn mặc định) | PR-26 | 10636 |
