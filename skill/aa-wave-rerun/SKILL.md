---
name: aa-wave-rerun
description: Runbook chạy lại pipeline A1→A3 (S1 rewrite, review, Master, atomize) cho một nước hoặc một nhóm tour trong AA-CIS — pilot 3 tour, expected_set, không merge giữa wave, đếm đúng, báo cáo 4 cột + Jev coverage, chờ duyệt giữa các wave. Dùng khi Nghiệp nói rerun, chạy lại <nước>, wave, pilot, hoặc AA-653.
---

# aa-wave-rerun

Dùng tạm cho tới khi AA-727 tự động hoá báo cáo wave. Khi AA-727 xong, thay mục 4–5 bằng endpoint.

## 1. Chuẩn bị

- [ ] `aa-session` đầu phiên đã chạy: STS, môi trường, api/worker cùng SHA.
- [ ] Jev canary `credit_ok`, số dư DFS đủ, cost guard (AA-649) còn budget ngày.
- [ ] Raw của nước đó đúng nguồn (ví dụ Bhutan dùng file `Bhutan (Newtemplate)`, 2 NCC). Chỗ nào chưa rõ → hỏi trước.
- [ ] Reset phạm vi khi cần: chỉ derived của nước đó, có RDS snapshot trước, chạy assert sau reset.
- [ ] **Ghi `expected_set`**: danh sách `tour_id` active của nước, lưu vào file trong `.tmp-session/` hoặc session log.

## 2. Pilot

- Chạy 3 tour, gồm ít nhất 1 tour dài và 1 tour khó (cycle/bike, raw ngắn).
- Báo cáo theo mục 5 → **chờ Nghiệp duyệt** rồi mới chạy phần còn lại.

## 3. Chạy wave

- **Không merge PR backend/pipeline trong lúc wave chạy.** PR FE thuần thì được.
- Theo dõi qua trang Jobs/Rewrite. S1 còn in-process cho tới khi AA-723 xong → không deploy API.
- `a3_atomize` cap 1 toàn hệ → 20–30 job xếp hàng mất khoảng 1 giờ, là bình thường.

## 4. Đếm đúng

Đếm theo **distinct tour** trong `expected_set`:

| Nhóm | Định nghĩa |
|---|---|
| Lên Master | `master_status='active'`, đã có bản publish mới của wave |
| Chờ duyệt | có dòng `review_queue` chưa dismissed (bản mới nhất) |
| Trash | raw bị trash vì không đủ dữ liệu |
| Interrupted / failed | job kết thúc lỗi hoặc bị huỷ |
| Chưa chạy | còn lại — **phải bằng 0** khi kết thúc wave |

- Không đếm bản superseded.
- `ingested` trong review ≠ chưa chạy.
- Tổng các nhóm = số tour trong `expected_set`.
- Tên bảng/cột chính xác (raw_tours.source_status, published_tours.master_status, v_active_tour_atoms, review_queue) đọc từ `docs/architecture/db-schema-reference.md` — không ghi cứng vào skill.

## 5. Báo cáo wave

```
Wave <nước> <dd/mm> — expected <n>
| S1 job ok | Lên Master | Chờ duyệt (tên + lý do + loại lỗi) | Atomized |
- Loại lỗi review: raw_insufficient / writer_tone / forbidden_word / transient
- Jev coverage: <tour có verdict thật>/<n> (đọc decision_log.zone, không đếm call)
- Chi phí: LLM $<x>, DFS $<y>
- Quality: phân bố điểm; brand audit fail
- Bất thường: <job interrupted, tour kẹt>
```

Rồi mới:
- Tour `transient` → regenerate.
- `writer_tone` / `forbidden_word` → không regenerate; gom vào AA-724 hoặc AA-641.
- `raw_insufficient` → trash.
- Báo cáo cho chị Thư → `aa-jira-update`.
