# AA-729: golden set 1.1.0 và baseline đầu tiên

Phiên S245, 20/10/2026. Tác nhân: Claude Code. Issue: AA-729. Bản tư vấn cho Nghiệp.

## Golden set

- Fixture `docs/eval/aa729/fixture-1.1.0.json`: 100 mẫu, seed 729. Không có PII (đã qua bước kiểm PII của `labels apply`).
- Phân bố: s1 50, t9 blog 15, t9 LinkedIn 15, t2 10, injection 10.
- Nguồn nhãn: agent panel 82 (Nghiệp duyệt), synthetic 10, admin edit 5, tenant edit 2, human label 1.
- Cách gắn nhãn panel: 3 giám khảo độc lập, cộng một lượt kiểm chứng đọc nguồn đầy đủ, xem [panel-report.md](panel-report.md).
  - 68 nhãn chốt ngay; 14 nhãn Nghiệp quyết trên trang duyệt, cả 14 theo đề xuất.
  - Nhãn và phiếu từng mẫu: [panel-labels.json](panel-labels.json).

| Nhóm | Đạt | Trượt |
|---|---|---|
| S1 (viết lại tour A1) | 6 | 44 |
| T2 (tenant viết lại) | 3 | 7 |
| Blog | 6 | 9 |
| LinkedIn | 10 | 5 |
| Injection | 0 | 10 |

## Baseline

Chạy trong một ECS task riêng (task def api:729), stage `adhoc_aa729`. Chi phí lấy từ `shared.llm_call_log`.

- **Score-only** (chấm lại văn bản đã đóng băng): $0,22. Run `8f07b98f`, [báo cáo](report-score-only.md).
- **Regenerate** (viết lại trên input đóng băng rồi chấm): $5,19. Run `dab254c4`, [báo cáo](report-regenerate.md).
- Tổng $5,41, trong trần $15 đã duyệt. Trước đó có một lượt chạy thử 3 mẫu, $0,13.

### Judge và gate so với nhãn người (score-only)

| Nhóm | Pipeline cho qua | Lệch so với nhãn | Lọt (nhãn Trượt mà pipeline cho qua) | Chặn oan (nhãn Đạt mà pipeline chặn) |
|---|---|---|---|---|
| S1 | 62,0% | 54,0% của 50 | 26 | 1 |
| T2 | 10,0% | 25,0% của 8 | 0 | 2 |
| Blog | 6,7% | 38,5% của 13 | 0 | 5 |
| LinkedIn | 33,3% | 53,8% của 13 | 0 | 7 |
| Injection | 0% | 0% | 0 | 0 |
| Tất cả | 38,0% | 43,6% của 94 | 26 | 15 |

**Đọc kết quả:**

1. **S1 lọt lỗi nhiều nhất.** 26/44 bản S1 mà người chấm Trượt vẫn được gate và judge cho qua. Các lớp lỗi bị lọt:
   - sai số ngày (tour 3 giờ bị chia thành Day 1–4);
   - bịa tên hoặc con số;
   - SEO meta bị cắt giữa câu;
   - từ khoá lạc đề.

   `validate` và judge `brand_fit` không có bộ phát hiện cho các lớp này.
2. **T9 thì ngược lại: chặn oan nhiều.** 5 blog và 7 LinkedIn mà người chấm Đạt vẫn bị gate chặn. Gate T9 đang quá chặt so với nhãn người.
3. **Injection: 10/10 bị chặn.** Ở mode regenerate, cả 10/10 được phòng thủ: không có canary, link hay markup bị chèn, không lộ prompt.
4. **Jev ở S1 regenerate chỉ khớp nhãn 12,5% (48 lần chạy).** Cần xem lại trong Q-6 (hiệu chỉnh).
5. **Ghi chép chi phí còn hở.** 116 lời gọi ở score-only và 188 ở regenerate không có dòng log. Báo cáo coi tổng `llm_call_log` là số chính thức. Tổng in-process ($0,21 + $5,00) gần khớp, nhưng phải đối chiếu với dashboard nhà cung cấp trước khi trích dẫn.

### Cách dùng

- Mọi thay đổi prompt, model hoặc ngưỡng của S1/T9 từ nay trích số trước/sau trên cùng fixture 1.1.0. Đây là dòng Done-when cuối của AA-729.
- Thiết kế hệ thống chất lượng dùng golden set này làm cổng hồi quy: [../2026-10-20-S245-quality-system/design.md](../2026-10-20-S245-quality-system/design.md).
