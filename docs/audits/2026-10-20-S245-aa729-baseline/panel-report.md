# AA-729: nhãn panel cho golden set 1.0.0

## Cách làm

1. Fixture 1.0.0 có 100 mẫu (seed 729): s1 50, t9 blog 15, t9 LinkedIn 15, t2 10, injection 10. Nguồn nhãn có sẵn: {'needs_panel': 82, 'admin_edit': 5, 'tenant_edit': 2, 'human_label': 1, 'synthetic': 10}.
2. 82 mẫu `needs_panel` được gửi cho 3 giám khảo độc lập, mỗi người một góc: đúng nguồn, giọng và cấu trúc, góc người đọc. Gói gửi không có kết luận của pipeline (passed, held, điểm, mã lỗi gate).
3. Giám khảo chỉ thấy đoạn trích nguồn 2.500 ký tự, trong khi 76/82 nguồn dài hơn (trung bình khoảng 11.000 ký tự). Vì vậy có thêm một lượt **kiểm chứng trên nguồn đầy đủ**, mỗi mẫu một agent: dò từng lỗi giám khảo nêu trong nguồn đầy đủ, rồi tự đọc tìm lỗi bị sót.
4. Nhãn **chốt** khi người kiểm chứng cùng kết luận với đa số giám khảo. Nhãn **cần anh quyết** khi người kiểm chứng lật kết luận của đa số.

## Kết quả

| Nhóm | Mẫu | Chốt: Đạt | Chốt: Trượt | Cần anh quyết |
|---|---|---|---|---|
| s1 | 50 | 6 | 37 | 7 |
| t2 | 7 | 3 | 3 | 1 |
| t9_blog | 12 | 1 | 6 | 5 |
| t9_linkedin | 13 | 9 | 3 | 1 |

- Chốt 68 mẫu: 58 mẫu cả 3 giám khảo cùng ý và người kiểm chứng xác nhận; 10 mẫu lệch phiếu nhưng người kiểm chứng đứng về phía đa số.
- Cần anh quyết 14 mẫu. Đề xuất chọn sẵn theo người kiểm chứng vì họ là người duy nhất đọc nguồn đầy đủ.
- Ở 26/82 mẫu, ít nhất một lỗi giám khảo nêu hoá ra có trong nguồn đầy đủ (đúng là do đoạn trích bị cắt). Sửa harness: gói gửi panel sẽ mang nguồn đầy đủ.

## Điều rút ra cho chất lượng (chưa phải baseline chấm máy)

- **S1 (viết lại tour A1)** trượt nhiều: 37/43 mẫu đã chốt là Trượt. Lỗi lặp lại:
  - đếm sai ngày (tour 3 giờ bị chia thành Day 1–4; tên tour 9 ngày nhưng nguồn là 10 ngày);
  - bịa con số hoặc tên sông, cấp thác ghềnh, hướng la bàn;
  - SEO meta bị cắt giữa câu;
  - từ khoá SEO lạc đề.
- **LinkedIn** khá tốt (9/12 mẫu chốt là Đạt). **Blog** chủ yếu Trượt (6/7 mẫu chốt).
- Đây là nhãn người/agent, dùng để đo các judge tự động trong baseline AA-729 (bước tiếp theo, có trả phí, trần $15).
