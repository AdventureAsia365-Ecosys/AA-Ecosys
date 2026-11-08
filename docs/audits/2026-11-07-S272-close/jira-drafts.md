# S272 — Nháp Jira (CHƯA ĐĂNG, chờ tech lead duyệt một lần)

**Trạng thái 08/11:** chưa đăng — tech lead dặn gom sang S273 (07/11 tối). Phiên S273 cập nhật số liệu theo snapshot mới rồi đưa duyệt một lần.

Gộp 4 nháp S271 (`docs/audits/2026-11-06-S271-writing-quality-audit/jira-drafts.md`) với việc đã ship ở S272. Luật: chỉ
báo việc đã ship và kiểm live; tag @thule bằng mention node; không mã nội bộ (AA-xxx, số PR), không câu hỏi cho chị, không
"ạ"; không quyết định kỹ thuật/hạ tầng (PR-27 không soạn). Số liệu lấy từ kiểm live ngày 07/11/2026.

Đã rà Jira (07/11 ~14:50 +07): `project in (PR, KAN, CON) AND statusCategory != Done`. Epic mới nhất đổi 06/11 06:25 (đợt
đăng S270); không có comment mới của chị Thư sau đó. PR-20 kỳ 4 (03–09/11) đến hạn từ thứ Hai 09/11 → soạn ở phiên đầu
tiên từ 09/11 (memory `platform-report-weekly`), không soạn ở đây.

## Ô tech lead chốt trước khi đăng

- [ ] #1 PR-22: bảng số liệu nền (blog 10 %, tour catalogue 48 %, tour đại lý 64 %) là số S271, chưa đo lại ở S272.
- [ ] #1 PR-22: câu "17/814 tour sẽ được giữ lại để xem" là kết quả chế độ báo cáo (chưa chặn thật) — giữ hay bỏ.
- [x] Câu "phiếu dữ kiện" (FactSheet) đã có bằng chứng: lần chạy thử 07/11 tối (1 tour đại lý + 3 bài T9) tạo 4
      phiếu, mọi bài mang mã phiếu, meta blog 147 ký tự; chi phí ~0,21 USD.
- [ ] #4 PR-23: bằng chứng là bài kiểm tự động trên hệ thống thử (69/69, gồm 2 bài kiểm tải về), chưa có ảnh chụp; nếu
      cần ảnh, phiên sau chụp màn hình tải về + thuộc tính file.

---

## 1. PR-22 — CIS: Nội dung & pipeline

@thule Cập nhật chất lượng viết bài (blog, bài mạng xã hội, tour):

- Đã rà soát toàn bộ cách hệ thống viết, chấm và kiểm bài, cho cả blog, tour catalogue và tour viết cho đại lý. Kết luận:
  giữ phần viết đang tốt, sắp xếp lại phần kiểm và sửa bài để không còn tình trạng sửa đi sửa lại.
- Đã chốt các quy tắc viết rõ ràng: được viết bối cảnh về địa danh, nhưng không bao giờ hứa hoạt động, dịch vụ, giờ giấc
  hay cảnh quan mà tour không có; câu về độ phù hợp với trẻ em, độ an toàn, nhịp độ chỉ được viết đúng như nguồn.
- Đã đưa lên hệ thống thử nghiệm:
  - bài viết không còn bị cắt giữa chừng vì hết giới hạn độ dài; lần sửa thứ ba không còn tốn tiền; tour có cưỡi voi được
    giữ nguyên văn và đưa vào hàng duyệt; số liệu chất lượng được đo mỗi đêm;
  - mỗi lần một bài đi ra (đăng, duyệt, sửa tay) đều được kiểm lần cuối và ghi lại kết quả. Lượt kiểm đầu trên 814 tour
    catalogue: 797 đạt, 17 tour sẽ được giữ lại để xem (9 tour có cưỡi voi, 6 tour lệch ngày so với nguồn, 3 tour thiếu
    một ngày so với thời lượng). Hiện mới ghi nhận, chưa chặn tour nào.
  - trước khi viết, hệ thống lập một "phiếu dữ kiện" cho mỗi tour/bài (lịch trình, bữa ăn, dịch vụ có trong nguồn);
    bài viết chỉ được dựa vào phiếu này. Đã chạy thử trên tour đại lý, blog và bài mạng xã hội: cả 4 bài đều dùng phiếu.
- Số liệu nền (8 tuần qua, dùng để so sánh các đợt sau):

| Loại bài | Đạt ngay lần viết đầu | Bị giữ lại để xem |
|---|---|---|
| Blog | 10% | 36% |
| Tour catalogue | 48% | 11% |
| Tour cho đại lý | 64% | 24% |

- Mục tiêu đợt tới: blog đạt ngay lần đầu từ 30% trở lên.

Kế hoạch các đợt tiếp theo em cập nhật dần ở đây.

---

## 2. PR-17 — Tenant viết lại tour đúng giọng thương hiệu

@thule Tour viết lại cho đại lý:

- Tour có hoạt động cưỡi voi: hệ thống giữ nguyên nội dung gốc, chỉ thêm phần thương hiệu của đại lý, và đưa vào hàng
  duyệt. Đại lý vẫn nhận bài như bình thường.
- Bước chấm giọng văn giờ chỉ để tham khảo, không còn quyết định số lần viết lại, nên bài ra nhanh hơn và ít tốn hơn.

---

## 3. PR-25 — Booking

@thule Booking: đã gỡ toàn bộ phần dành cho khách lẻ (B2C) khỏi hệ thống, đúng mô hình chỉ bán cho đại lý. Dữ liệu cũ của
phần này sẽ được xoá hẳn từ 28/11 sau thời gian giữ an toàn 30 ngày.

---

## 4. PR-23 — Portal tenant / app cho đại lý

@thule Nhãn "nội dung do AI tạo" khi đại lý tải bài về:

- Từ nay mọi bản tải về trong Content studio (bài blog dạng trang web, đoạn chèn, bản chữ, và file Word của tour) đều mang
  nhãn máy đọc được cho biết nội dung do AI tạo, đúng yêu cầu ghi nhãn nội dung AI của châu Âu (hạn 02/12/2026).
- File Word của tour giờ được lưu đúng tên tour và phiên bản, không còn tất cả cùng tên "tour.docx".
- Đã kiểm tự động trên hệ thống thử: tải bài blog, đoạn chèn, bản chữ và file Word, nhãn và tên file đều đúng.
