# AA-790 vòng 9 — brief bám dữ kiện chuyến đi (trip-facts grounding), A/B + panel mù (S256, 29/10/2026)

**Kết luận: FAIL → cờ `T9_BRIEF_GROUNDING_MODE` giữ tắt; vòng 6 vẫn live.**

- Code: CIS #1108 (`d3ae3468`), cờ mặc định tắt, prompt khi tắt giống từng byte (hash 192 prompt ghim trong test).
- Chạy: 8 bài (5 blog + 3 LinkedIn, 3 tenant), cùng góc T8 tái sinh một lần; arm r9c (đối chứng), r9c2 (lặp lại để đo nhiễu), r9 (bật grounding). Grounding đổi brief ở 8/8 bài.
- Chi phí (llm_call_log, stage adhoc_aa790): r9c $0,46 (T8 $0,13 + viết $0,33), r9c2 $0,33, r9 $0,31 → **$1,10** (trần $1,70).
- Panel mù 4 góc (S251 rubric), 32 item (r6 lưu sẵn + 3 arm), 16 lượt chấm.

| Ngưỡng (đặt trước khi chạy) | Kết quả |
|---|---|
| source_fidelity r9 − r9c > max(nhiễu, 0,15) | **+0,50** PASS |
| reader_value r9 − r9c ≥ −max(nhiễu, 0,15) | **−0,25** < −0,19 FAIL |
| brand_voice r9 − r9c ≥ −max(nhiễu, 0,15) | +0,38 PASS |
| ai_tells r9 ≥ 5,5 và không giảm quá nhiễu | 5,62 / +0,31 PASS |
| ≥ một nửa brief đổi | 8/8 PASS |

Nhận xét: grounding làm bài bám nguồn hơn rõ (+0,5) nhưng bài kém hữu ích cho người đọc (bớt thông tin thực hành). Đòn bẩy kế: giữ grounding, thêm checklist reader-value (câu hỏi khách hay hỏi, thông tin thực hành) vào brief, chạy lại cùng harness. Brand voice theo tenant (Done-when ≥ 7 mỗi tenant): Terra Family 6,62, Trail Pulse 5,25, WildKind 7,5 → chưa đạt.

Chi tiết: `aggregate-output.txt`, `panel-scores.json`, `aggregate_r9.py`, `build_blind_r9.py`.
