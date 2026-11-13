# Platform › Settings giải thích từng cài đặt (AA-1096, lane l23, S279)

*13/11/2026, ảnh chụp cho tech lead. Chụp trên máy local trước khi merge: `next dev` của nhánh code CIS chạy với một API
giả (dữ liệu bịa, nhân viên "Linh Tran" là tên bịa), các định nghĩa và phần giải thích lấy từ `compiled_defaults.json`
của nhánh migration CIS 415. Trang staff CIS chưa kiểm được trên Dev trước khi merge (skill aa-ui-verify); sau deploy
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

Console: 0 lỗi ở cả 4 lượt (1440/390 × sáng/tối).

## Kiểm sau deploy (live_steps)

- Migration CIS 415 được Migration Apply áp (class contract), rồi deploy CIS api + admin.
- Platform › Settings: mỗi khoá có dòng "điều chỉnh gì" và nút Explain mở đủ 5 phần (28 khoá CIS).
- Hộp thoại Change của "Blog length per source word": gõ `3,364`, không có lỗi (không lưu).
- Booking › Pricing › Policy: mỗi tham số có phần giải thích (39 tham số).
