# Platform › Settings giải thích từng cài đặt (AA-1096, lane l23, S279)

*13/11/2026, ảnh chụp cho tech lead. Chụp trên máy local trước khi merge: `next dev` của nhánh code CIS chạy với một API
giả (dữ liệu bịa, nhân viên "Linh Tran" là tên bịa), các định nghĩa và phần giải thích lấy từ `compiled_defaults.json`
của nhánh migration CIS 416 (lượt đầu đánh số 415; lượt sửa đổi sang 417; lượt tiếp tục 13/11 chốt 416). Trang staff CIS chưa kiểm được trên Dev trước khi merge (skill aa-ui-verify); sau deploy
cần chụp lại bằng phiên E2E admin.*

Phản hồi của tech lead: "các ngưỡng ở Settings nhìn khó hiểu, phải giải thích hay định nghĩa là gì thì mới biết khi
cần chỉnh". Hai lỗi thấy cùng ngày: ô số không nhận `3,364` ("Enter a number"), cột Last change hiện UUID của người
duyệt.

## Ảnh

| Ảnh | Nội dung |
|---|---|
| `settings-desktop-light-overview.png`, `settings-desktop-dark-overview.png` | 1440 px: nhãn mới (không còn mã T7/T9/A1/T2), dòng "điều chỉnh gì" ngắn dưới nhãn (tối đa 2 dòng, đủ chữ ở tooltip), khoá nhỏ, nút Explain |
| `settings-desktop-*-explained.png` | Mở Explain của "Blog length per source word": What it controls / If you raise it / If you lower it / When to change it / Example (at the default), ghi chú kỹ thuật thu gọn |
| `settings-desktop-light-explained-vi.png` | Cùng phần giải thích bằng tiếng Việt (chuyển VI trên thanh trên) |
| `settings-mobile-*-overview.png`, `settings-mobile-*-explained.png` | 390 px, sáng và tối; đo `main` và trang: không tràn ngang (0 px) |
| `settings-change-dialog-guide-*.png` | Hộp thoại Change: phần giải thích nằm trên các ô nhập |
| `settings-change-dialog-3364-*.png` | Gõ `3,364`: được nhận là 3.364, không còn "Enter a number", nút Save and approve bật (không bấm lưu) |
| `settings-last-change-name.png` | Cột Last change hiện tên nhân viên ("Linh Tran"), mã nhân viên nằm trong tooltip |
| `booking-policy-layout-mock-1440-light.png`, `booking-policy-layout-mock-390-light.png` | Booking › Pricing › Policy trên bản build production với API giả của layout-mock (chữ giải thích trong ảnh là chữ bịa của fixture): dòng "điều chỉnh gì" và nút Explain mỗi tham số; layout-mock 12/12 xanh (1440/1400/1280/960/390, không tràn ngang) |

Console: 0 lỗi ở cả 4 lượt CIS (1440/390 × sáng/tối).

## Lượt sửa sau review (fix pass, 13/11/2026)

Reviewer độc lập nêu 7 điểm; đã sửa cả 7:

- Nhánh migration rebase lên main có CIS 412-413 (151 khoá chất lượng, nhãn có mã, chưa có giải thích). Thay vì cho vào
  baseline, mọi khoá đều có nhãn dễ đọc và giải thích EN + VI: 28 khoá cũ + 151 khoá chất lượng + 17 khoá TripPlanner
  (CIS 414, lane l21) + 5 khoá bài thử bộ kiểm khẳng định (CIS 416, lane l22) = 201 khoá. Migration đổi số 415 → 417
  (l21 giữ 414-415, l22 giữ 416); nhánh mang theo commit của l21/l22 để guard và post-check thấy khoá của họ.
- 81 khoá "Quality check mode" ghi rõ: chế độ không đổi cách xử lý bài (lượt review thứ hai sửa tiếp: cũng không đổi
  báo cáo hay đánh giá) (đã kiểm code: `registry.classes()` chỉ dùng mode để suy ra bước kiểm chính của loại lỗi).
- "Tour rewrite attempts before human review": ghi rõ bộ viết hiện tại (chế độ contract, Dev đang chạy) tự quyết số lần
  viết lại và bỏ qua con số này; chỉ luồng chấm điểm cũ đọc nó.
- "Agency tour rewrite: voice checks per version": bỏ câu "kiểm tra lần hai cho báo cáo ổn định hơn"; lần thứ hai chỉ
  dùng khi job chạy lại.
- Ví dụ không còn "Today ..." mà "With the default of ..." (CIS) / "Starting value ..." (Booking). Với 4 khoá phụ thuộc
  giá trị khác (từ nguồn của Blog, tỷ lệ ký tự mỗi từ, độ giống khi xoá câu lặp, tỷ lệ nhắm độ dài blog) trang tính thêm
  dòng "In force now" từ giá trị đang áp dụng, và hộp thoại Change tính dòng "With the value you enter" cho giá trị đang
  gõ.
- Booking: danh sách / bảng không còn tiêu đề "The stricter / looser choice" (hai đoạn chữ nói ngược tiêu đề); nay là
  "If you add more or make it bigger" / "If you remove some or make it smaller", chữ không còn nêu bên nào chặt hơn.

| Ảnh (lượt sửa) | Nội dung |
|---|---|
| `fix-desktop-light-in-force-line.png`, `fix-desktop-dark-in-force-line.png`, `fix-mobile-light-in-force-line.png` | "Blog length per source word" đang áp dụng 3,364 (API giả): ví dụ ghi mặc định 5,8, dòng "In force now" tính 1.398 từ nguồn |
| `fix-desktop-light-in-force-line-vi.png` | Cùng dòng bằng tiếng Việt ("Đang áp dụng") |
| `fix-change-dialog-draft-line.png` | Hộp thoại Change, gõ `3,0`: dòng "With the value you enter" tính 1.567 từ nguồn (không lưu) |
| `fix-*-check-modes-overview.png`, `fix-*-check-mode-explained.png`, `fix-desktop-light-check-mode-explained-vi.png` | Tab quality_detectors: nhãn "Quality check mode: ..." thay cho "fact.number · F1_grounding"; giải thích (chụp lại ở lượt review thứ hai) nói rõ chế độ chỉ đánh dấu bước kiểm chính của loại lỗi, không đổi bài, điểm, giữ bài, báo cáo hay đánh giá |
| `fix-tripplanner-overview.png` | Tab TripPlanner: 17 khoá có dòng "điều chỉnh gì" |

Console: 0 lỗi; không tràn ngang (1440 sáng/tối, 390 sáng). Ảnh Booking không chụp lại (đổi chữ tiêu đề và ví dụ; bố cục
không đổi).

## Kiểm sau deploy (live_steps)

- Migration CIS 416 được Migration Apply áp (class contract; 412-415 đã có trên Dev), rồi deploy CIS api + admin.
- Platform › Settings: mỗi khoá có dòng "điều chỉnh gì" và nút Explain mở đủ 5 phần (179 khoá CIS + 17 khoá
  TripPlanner).
- Hộp thoại Change của "Blog length per source word": gõ `3,364`, không có lỗi (không lưu).
- Booking › Pricing › Policy: mỗi tham số có phần giải thích (39 tham số).

## Lượt tiếp tục (13/11/2026, sau khi main có CIS 412-415)

- Nhánh migration merge main (CIS 412-415 đã áp trên Dev, code chất lượng và saga đã merge). Migration giải thích đổi số
  417 → 416 và chỉ phủ khoá đã có trên main: 28 + 151 + 17 = 196 khoá, khoá nào cũng có nhãn dễ đọc và giải thích
  EN + VI (lint với baseline rỗng xanh).
- 5 khoá bài thử bộ kiểm khẳng định (lane l22) rời nhánh này; lane đó ship sau dưới số 417 và tự mang giải thích trên
  dòng seed (chữ đã viết ở lượt sửa đầu của lane này, đã giao lại cho lane đó).
- Giao diện không đổi, nên không chụp lại ảnh.

## Lượt review thứ hai (13/11/2026)

Reviewer độc lập đối chiếu chữ giải thích với code, nêu 5 điểm; cả 5 đúng và đã sửa trong migration CIS 416
(`compiled_defaults.json` sinh lại):

- Ngưỡng đề xuất chủ đề theo kênh (8 khoá): `needs_said` là số ký tự lịch trình viết về khoảnh khắc đó, cộng dồn mọi tour
  (`atom_ranking.py`: `SUM(LENGTH(COALESCE(evidence, text)))`), không phải "số lần nhắc"; ví dụ đổi thành "ít nhất 150 ký
  tự mô tả trong lịch trình".
- `most_per_hub` (5 khoá có giới hạn hub) được giải thích riêng: 0 chặn mọi chủ đề thuộc một hub, số cao hơn là nới hơn
  (`slate.py` từ chối khi đã đủ số chủ đề của hub). "0 = không có ngưỡng" chỉ còn áp cho các số needs_*.
- 81 khoá chế độ bước kiểm: code chỉ dùng chế độ để suy ra bước kiểm chính (`owner_gates`), và chỉ lint chất lượng đọc nó
  (cảnh báo khi một loại lỗi nghiêm trọng không còn bước kiểm nào ở enforce). Chữ cũ nói báo cáo và đánh giá thay đổi là
  sai; nay ghi rõ không đổi gì ở bài, điểm, giữ bài, báo cáo hay đánh giá. "golden-set" đổi thành "một lần chạy đánh giá
  trên một bộ bài đã được duyệt cố định".
- 2 khoá giới hạn lead của TripPlanner (`send`, `send_ip`) không gọi model: tăng / giảm / khi nào nay nói về lead giả đổ
  vào hộp thư và CRM của đại lý, không còn "lượt gọi có phí" hay "nhật ký gọi AI".
- Ví dụ tiếng Việt của 6 giới hạn theo khung giờ / phút đặt số thứ tự đúng chỗ ("lead thứ 6 trong cùng một giờ").

| Ảnh | Nội dung |
|---|---|
| `review2-en-topic-bar-explained.png`, `review2-vi-topic-bar-explained.png` | "Topic planning: bar for Facebook" mở Explain: needs_said tính bằng ký tự, most_per_hub giải thích riêng |
| `review2-en-lead-limit-explained.png`, `review2-vi-lead-limit-explained.png` | "Leads per visitor session per hour": lead giả, hộp thư và CRM của đại lý; ví dụ VI "lead thứ 6 trong cùng một giờ" |

Các ảnh `fix-*-check-mode*.png` ở trên đã chụp lại với chữ mới. Console: 0 lỗi; không tràn ngang.
