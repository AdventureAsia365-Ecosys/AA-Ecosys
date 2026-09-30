# Jira PR-13 — nháp (chờ anh Nghiệp duyệt, CHƯA đăng)

**Loại:** Story · **Project:** PR · **Tiêu đề:** Jev (TypeSafe) — decision layer cho content pipeline: mỗi stage hỏi Jev những gì

---

## Mô tả

Jev đã chạy trong content pipeline như một **decision layer**: trả lời các câu hỏi ngắn có kiểu (yes/no, chọn 1) về dữ liệu **trước khi** mình trả tiền mua hoặc tính điểm. Jev không viết văn bản.

**Đang chạy trên Dev**
- **Kiểm keyword trước khi mua search data:** với mỗi keyword đề xuất cho một địa điểm, hỏi *"keyword này có đúng về địa điểm này, không chỉ là loại chung?"* trước khi mua DataForSEO. Keyword Jev chắc chắn "không" sẽ không mua (vd "hot springs" cho một onsen cụ thể, "peninsula" cho Kii Peninsula).
  - Đã calibrate trên 200 cặp địa điểm/keyword thật, gán nhãn và kiểm bằng người: mọi cặp Jev chấm ≤ 0.30 đều đúng là không khớp (55/55).
- **4 câu hỏi khác đang ở chế độ shadow** (chỉ ghi lại, chưa tác động):
  - keyword idea là tìm kiếm của du khách hay tìm khách sạn/đặt chỗ;
  - khi upload: dòng có phải tour không, itinerary có nội dung từng ngày không, tour ở nước nào.
- **Trang admin "Jev Decisions"** (Operations): mỗi stage hỏi câu gì, có đang dùng không, câu trả lời rơi vào đâu, chi phí bao nhiêu. Chi phí Jev cũng hiện trong External Spend. Tổng chi phí Jev tới nay: dưới $0.01.

**Nguyên tắc**
- Jev chỉ tác động khi chắc chắn **và** câu hỏi đã được calibrate trên dữ liệu thật có nhãn. Khi Jev không chắc hoặc không gọi được, stage giữ luật cũ.
- Không xoá dữ liệu, không gỡ nội dung đã publish. Mọi câu trả lời đều được lưu, nên có thể dời ngưỡng sau mà không phải hỏi lại.
- Nội dung của tenant chỉ gửi cho Jev với tenant test của mình, cho tới khi có thoả thuận xử lý dữ liệu (DPA) với TypeSafe.

**Đính kèm:** `jev-review-for-thu.xlsx` — toàn bộ câu hỏi Jev theo từng stage/node, 12 quyết định đã chốt và 6 câu hỏi cho chị. Các cột màu vàng để chị điền ý kiến hoặc sửa trực tiếp.

---

## Câu hỏi cho chị Thư (có trong sheet "Hoi chi Thu")

1. **Ngưỡng keyword:** bên em loại ở ≤ 0.30 (200 cặp có nhãn); nhánh của chị dùng 0.15 (1.070 keyword chưa nhãn). Bên em giữ 0.30 và hạ dần về 0.15 khi thấy loại nhầm đầu tiên — chị đồng ý không?
2. **Câu hỏi chung chung:** bên em áp dụng quy tắc marketing của chị (câu không nêu nơi nào, hỏi được cho mọi nước thì không tính điểm) cho toàn platform — vẫn đúng ý chị?
3. **Phạm vi quốc gia:** chị xét theo quốc gia của cả export (Nhật). Bên em có 21 nước chung một pool nên xét theo quốc gia các tour của khoảnh khắc đó — OK không?
4. **Câu hỏi landing:** blind sample của chị đồng thuận 51%. Bên em chấm lại ~200 cặp cùng loại (đền↔đền, lâu đài↔lâu đài), câu hỏi cho người chấm y hệt câu gửi Jev — chị muốn đổi gì?
5. **Chống bịa ở bước viết:** bên em thêm bước kiểm master content có đúng nguồn không (số liệu bằng luật, câu khác bằng Jev). Bước viết của chị có kiểm từng câu không, làm thế nào?
6. **DPA:** ai liên hệ TypeSafe về thoả thuận xử lý dữ liệu / zero-retention để mở Jev cho tenant thật?
