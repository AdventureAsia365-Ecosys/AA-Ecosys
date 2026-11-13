# Platform › Settings giải thích từng cài đặt (AA-1096, lane l23, S279)

*13/11/2026, ảnh chụp cho tech lead. Chụp trên máy local trước khi merge: `next dev` của nhánh code CIS chạy với một API
giả (dữ liệu bịa, nhân viên "Linh Tran" là tên bịa), các định nghĩa và phần giải thích lấy từ `compiled_defaults.json`
của nhánh migration CIS 417 (lượt đầu đánh số 415; lượt sửa đổi sang 417). Trang staff CIS chưa kiểm được trên Dev trước khi merge (skill aa-ui-verify); sau deploy
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
- 81 khoá "Quality check mode" ghi rõ: chế độ chỉ đổi cách báo cáo chất lượng và đánh giá tính bước kiểm, không đổi
  cách xử lý bài (đã kiểm code: `registry.classes()` chỉ dùng mode để suy ra bước kiểm chính của loại lỗi).
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
| `fix-*-check-modes-overview.png`, `fix-*-check-mode-explained.png`, `fix-desktop-light-check-mode-explained-vi.png` | Tab quality_detectors: nhãn "Quality check mode: ..." thay cho "fact.number · F1_grounding", giải thích nói rõ chỉ ảnh hưởng báo cáo |
| `fix-tripplanner-overview.png` | Tab TripPlanner: 17 khoá có dòng "điều chỉnh gì" |

Console: 0 lỗi; không tràn ngang (1440 sáng/tối, 390 sáng). Ảnh Booking không chụp lại (đổi chữ tiêu đề và ví dụ; bố cục
không đổi).

## Kiểm sau deploy (live_steps)

- Migration CIS 414-417 được Migration Apply áp (class contract, theo thứ tự), rồi deploy CIS api + admin.
- Platform › Settings: mỗi khoá có dòng "điều chỉnh gì" và nút Explain mở đủ 5 phần (184 khoá CIS + 17 khoá
  TripPlanner).
- Hộp thoại Change của "Blog length per source word": gõ `3,364`, không có lỗi (không lưu).
- Booking › Pricing › Policy: mỗi tham số có phần giải thích (39 tham số).
